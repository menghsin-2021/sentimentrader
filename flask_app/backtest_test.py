import pandas as pd #引入pandas讀取股價歷史資料CSV檔
import requests
import pandas as pd
from io import StringIO
import datetime
import os
#visual
import matplotlib.pyplot as plt
import mplfinance as mpf
import config
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from pprint import pprint
import talib
import numpy as np

# db var
DBHOST = config.DBHOST
DBUSER = config.DBUSER
DBPASSWORD = config.DBPASSWORD
DBNAME = config.DBNAME
TABLES = "daily_stock_price"
RDSPORT = 3306



form = {'category': 'sail',
            'discount': '40',
            'end_date': '2020-11-10',
            'money': '500',
            'sentiment_para_less': '40',
            'sentiment_para_more': '60',
            'source': 'ptt',
            'start_date': '2018-01-01',
            'stock_code': '2603',
            'strategy_in': 'increase_in',
            'strategy_in_para': '1',
            'strategy_line': 'none_line',
            'strategy_out': 'decrease_out',
            'strategy_out_para': '1',
            'strategy_sentiment': 'daily_sentiment_pass'}
pprint(form)
# category and stock_code
category = form['category']
stock_code = form['stock_code']
print('category:', category)
print('stock_code:', stock_code)
# duration
start_date = form['start_date']
end_date = form['end_date']
print('start_date:', start_date)
print('end_date:', end_date)
# KD, MACD, or custom
strategy_line = form['strategy_line']
print('strategy_line:', strategy_line)
# market in: custom para
strategy_in = form['strategy_in']
strategy_in_para = float(form['strategy_in_para'])
print('strategy_in:', strategy_in)
print('strategy_in_para:', strategy_in_para)
# market out: custom para
strategy_out = form['strategy_out']
strategy_out_para = float(form['strategy_out_para'])
print('strategy_out:', strategy_out)
print('strategy_out_para:', strategy_out_para)
# transition stop
strategy_sentiment = form['strategy_sentiment']
sentiment_para_less = float(form['sentiment_para_less'])
sentiment_para_more = float(form['sentiment_para_more'])
print('strategy_sentiment:', strategy_sentiment)
print('sentiment_para_less:', sentiment_para_less)
print('sentiment_para_more:', sentiment_para_more)
print((float(sentiment_para_more) / 100 * 10 - 5))
print((float(sentiment_para_less) / 100 * 10 - 5))
# your fee discount
source = form['source']
print('source:', source)
# your fund
money = form['money']
print('money:', money)
# your fee discount
discount = form['discount']
print('discount:', discount)

engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                           .format(user=DBUSER,
                                   pw=DBPASSWORD,
                                   db=DBNAME,
                                   host=DBHOST))

connection = engine.connect()


# set date
start_date_datetime = datetime.fromisoformat(start_date)
end_date_datetime = datetime.fromisoformat(end_date)
print(start_date_datetime)
print(end_date_datetime)


resoverall_stock_price = connection.execute("SELECT DATE_FORMAT(date,'%%Y-%%m-%%d') AS Date, open AS Open, high AS High, \
                                             low AS Low, close AS Close, volume AS Volume \
                                             FROM sentimentrader.daily_stock_price \
                                             WHERE stock_code = '{}' \
                                             AND `date` BETWEEN '{}' and '{}' \
                                             ORDER BY `Date`".format(stock_code, start_date_datetime, end_date_datetime))


# fetch stock price
df1 = pd.DataFrame(resoverall_stock_price.fetchall())
df1.columns = resoverall_stock_price.keys()


# create df1
df1 = df1.drop_duplicates(subset='Date')
df1.index = df1['Date']
df1_date_index = df1.drop(['Date'], axis=1)
print(df1_date_index)


# create df2 and concat
if strategy_sentiment == 'none_pass':
    # 不需要 concate
    df = df1_date_index

else:
    # 和 sentiment concate
    resoverall_sentiment = connection.execute("SELECT DATE_FORMAT(date,'%%Y-%%m-%%d') AS Date, (avg_valence - 5) as avg_valence, (avg_arousal - 5) as avg_arousal, sum_sentiment \
                                FROM sentimentrader.daily_sentiment \
                                WHERE source = '{}' \
                                AND stock_code = '{}' \
                                AND `date` BETWEEN '{}' and '{}' \
                                ORDER BY `Date`".format(source, stock_code, start_date_datetime, end_date_datetime))

    df2 = pd.DataFrame(resoverall_sentiment.fetchall())
    df2.columns = resoverall_sentiment.keys()

    df2 = df2.drop_duplicates(subset='Date')
    df2.index = df2['Date']
    df2_date_index = df2.drop(['Date'], axis=1)

    df = pd.concat([df1_date_index, df2_date_index], axis=1)
    df = df.reindex(df1_date_index.index)
    df = df.dropna()

# change astype
df['Volume'] = df['Volume'].astype('int')
print(df)



# 進場時機判定
if strategy_line == 'macd_line':
    pass

# KD line
elif strategy_line == 'kdj_line':
    df["K"], df["D"] = talib.STOCH(df['High'],
                                   df['Low'],
                                   df['Close'],
                                   fastk_period=9,
                                   slowk_period=3,
                                   slowk_matype=1,
                                   slowd_period=3,
                                   slowd_matype=1)

    df["B_K"] = df["K"].shift(1)
    df["B_D"] = df["D"].shift(1)

    # only KD
    if strategy_sentiment == 'none_pass':
        buy = []
        sell = []
        buy_count = 0
        for i in range(len(df)):
            if df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                buy.append(1)
                sell.append(0)
                buy_count += 1

            elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                sell.append(-1)
                buy.append(0)
                buy_count -= 1

            else:
                buy.append(0)
                sell.append(0)

        df["buy"] = buy
        df["sell"] = sell

    # KD + sentiment over less
    elif strategy_sentiment == 'daily_sentiment_pass':
        buy = []
        sell = []
        buy_count = 0
        for i in range(len(df)):
            if df['avg_valence'][i] < (float(sentiment_para_more) / 100 * 10 - 5) and df['avg_valence'][i] > (float(sentiment_para_less) / 100 * 10 - 5):
                if df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1

                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1

                else:
                    buy.append(0)
                    sell.append(0)
            else:
                buy.append(0)
                sell.append(0)

        df["buy"] = buy
        df["sell"] = sell

    # KD + sentiment to negative
    elif strategy_sentiment == 'to_negative_pass':
        buy = []
        sell = []
        buy_count = 0
        for i in range(len(df)):
            if i > 0 and df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
                if df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1

                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1

                else:
                    buy.append(0)
                    sell.append(0)
            else:
                buy.append(0)
                sell.append(0)

        df["buy"] = buy
        df["sell"] = sell

    # KD + sentiment to positive
    elif strategy_sentiment == 'to_positive_pass':
        buy = []
        sell = []
        buy_count = 0
        for i in range(len(df)):
            if i > 0 and df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
                if df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1

                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1

                else:
                    buy.append(0)
                    sell.append(0)
            else:
                buy.append(0)
                sell.append(0)

        df["buy"] = buy
        df["sell"] = sell


# 使用者自訂 strategy_line == 'none_line'
else:
    if strategy_in == 'increase_in':
        # only incease_in
        if strategy_sentiment == 'none_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 1:
                    if df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)
            df["buy"] = buy
            df["sell"] = sell
        # increase_in + sentiment over less pass
        elif strategy_sentiment == 'daily_sentiment_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if df['avg_valence'][i] < (float(sentiment_para_more) / 100 * 10 - 5) and df['avg_valence'][i] > (
                        float(sentiment_para_less) / 100 * 10 - 5):
                    if df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell

        # increase_in + sentiment to negative
        elif strategy_sentiment == 'to_negative_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 0 and df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
                    if df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell

        # increase_in + sentiment to positive
        elif strategy_sentiment == 'to_positive_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 0 and df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
                    if df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell

    # strategy_in == 'increase_out'
    else:
        # only incease_out
        if strategy_sentiment == 'none_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 1:
                    if df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)
            df["buy"] = buy
            df["sell"] = sell
        # increase_out + sentiment over less pass
        elif strategy_sentiment == 'daily_sentiment_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if df['avg_valence'][i] < (float(sentiment_para_more) / 100 * 10 - 5) and df['avg_valence'][i] > (
                        float(sentiment_para_less) / 100 * 10 - 5):
                    if df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell

        # increase_out + sentiment to negative
        elif strategy_sentiment == 'to_negative_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 0 and df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
                    if df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell

        # increase_out + sentiment to positive
        elif strategy_sentiment == 'to_positive_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 0 and df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
                    if df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1

                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1

                    else:
                        buy.append(0)
                        sell.append(0)
                else:
                    buy.append(0)
                    sell.append(0)

            df["buy"] = buy
            df["sell"] = sell


print(df)


# tag buy marker
buy_mark = []
for i in range(len(df)):
    if df["buy"][i] == 1:
        buy_mark.append(df["High"][i] + 15)
    else:
        buy_mark.append(np.nan)
df["buy_mark"] = buy_mark


# tag sell marker
sell_mark = []
for i in range(len(df)):
    if df["sell"][i] == -1:
        sell_mark.append(df["Low"][i] - 15)
    else:
        sell_mark.append(np.nan)
df["sell_mark"] = sell_mark



# df.index = pd.DatetimeIndex(df.index)
# stock_id = "{}.TW".format(stock_code)
# mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
# s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
# add_plot =[mpf.make_addplot(df["buy_mark"],scatter=True, markersize=100, marker='v', color='r'),
#            mpf.make_addplot(df["sell_mark"],scatter=True, markersize=100, marker='^', color='g'),
#            mpf.make_addplot(df["avg_valence"],panel= 2,color="g")]
# kwargs = dict(type='candle', volume = True,figsize=(20, 10),title = stock_id, style=s,addplot=add_plot)
# mpf.plot(df, **kwargs)



# 計算買進和賣出次數
buy1 = df.loc[df["buy"] == 1]
sell1 = df.loc[df["sell"] == -1]
print("買進次數 : " + str(len(buy1)) + "次")
print("賣出次數 : " + str(len(sell1)) + "次")







