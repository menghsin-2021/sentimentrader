import pandas as pd #引入pandas讀取股價歷史資料CSV檔
import requests
from io import StringIO
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
            'end_date': '2021-11-10',
            'money': '500',
            'sentiment_para_less': '40',
            'sentiment_para_more': '60',
            'source': 'ptt',
            'start_date': '2020-01-01',
            'stock_code': '2317',
            'strategy_in': 'increase_in',
            'strategy_in_para': '1',
            'strategy_line': 'kdj_line',
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
set_money = int(form['money'])
print('set_money:', set_money)
# your fee discount
discount = float(form['discount'])
print('discount:', discount)

duration_day = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date))
print('duration_day: ', duration_day)
duration_year = round(duration_day.days / 365, 2)
print('duration_year: ', duration_year)
print(type(duration_year))

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
money = set_money
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
            if money >= df["Close"][i] and df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                buy.append(1)
                sell.append(0)
                buy_count += 1
                money -= df["Close"][i]
            elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                sell.append(-1)
                buy.append(0)
                buy_count -= 1
                money += df["Close"][i]
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
                if money >= df["Close"][i] and df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1
                    money -= df["Close"][i]
                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1
                    money += df["Close"][i]
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
                if money >= df["Close"][i] and df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1
                    money -= df["Close"][i]
                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1
                    money += df["Close"][i]
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
                if money >= df["Close"][i] and df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
                    buy.append(1)
                    sell.append(0)
                    buy_count += 1
                    money -= df["Close"][i]
                elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
                    sell.append(-1)
                    buy.append(0)
                    buy_count -= 1
                    money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
                    if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                        buy.append(1)
                        sell.append(0)
                        buy_count += 1
                        money -= df["Close"][i]
                    elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                            df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                        sell.append(-1)
                        buy.append(0)
                        buy_count -= 1
                        money += df["Close"][i]
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
        buy_mark.append(df["High"][i] + 10)
    else:
        buy_mark.append(np.nan)
df["buy_mark"] = buy_mark


# tag sell marker
sell_mark = []
for i in range(len(df)):
    if df["sell"][i] == -1:
        sell_mark.append(df["Low"][i] - 10)
    else:
        sell_mark.append(np.nan)
df["sell_mark"] = sell_mark


if strategy_line == 'kdj_line' and strategy_sentiment != 'none_pass':
    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),
                mpf.make_addplot(df["K"], panel=2, color="r"),
                mpf.make_addplot(df["D"], panel=2, color="g"),
                mpf.make_addplot(df["avg_valence"], panel=2, color="b")
                ]

elif strategy_line == 'kdj_line' and strategy_sentiment == 'none_pass':
    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),
                mpf.make_addplot(df["K"], panel=2, color="r"),
                mpf.make_addplot(df["D"], panel=2, color="g")
                ]

elif strategy_sentiment != 'none_pass':
    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),
                mpf.make_addplot(df["avg_valence"], panel=2, color="b")
                ]

else:
    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),]

df.index = pd.DatetimeIndex(df.index)
stock_id = "{}.TW".format(stock_code)
mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
kwargs = dict(type='candle', volume=True, figsize=(20, 10),title = stock_id, style=s, addplot=add_plot)
filename = stock_code + '_' + datetime.today().strftime('%Y-%m-%d')
mpf.plot(df, **kwargs, savefig=filename)



# 計算買進和賣出次數
buy1 = df.loc[df["buy"] == 1]
sell1 = df.loc[df["sell"] == -1]
print("買進次數 : " + str(len(buy1)) + "次")
print("賣出次數 : " + str(len(sell1)) + "次")

sell1 = sell1.append(df[-1:])
print(sell1.tail())

money = set_money
print('資金: ', money)
for i in range(len(sell1)-1):
    money = money - buy1["Close"][i] + sell1['Close'][i] - ((buy1["Close"][i] + sell1["Close"][i]) * 0.001425 * discount / 100)

final_money = money + (len(buy1) - len(sell1)) * df["Close"][-1]

print('最後所得金額: ', final_money)
print('淨收益: ', final_money - set_money)
print('總報酬率(淨收益) = ', (final_money - set_money) / set_money * 100, '%')

return_rate = []
for i in range(len(buy1)):
    if i < len(sell1):
        rate = round((sell1["Close"][i] - buy1["Close"][i]) / buy1["Close"][i] * 100, 2)
        return_rate.append(rate)
    # >= len(sell1)
    else:
        rate = round((df["Close"][-1] - buy1["Close"][i]) / buy1["Close"][i] * 100, 2)
        return_rate.append(rate)

print('每次交易(買+賣)報酬率:', return_rate)

return_all = sorted(return_rate, reverse=True)
print('每次交易報酬率排序:', return_all)
print("該策略最高報酬為 : " + str(return_all[0]) + " %")
print("該策略最低報酬為 : " + str(return_all[-1]) + " %")

win = len([i for i in return_rate if i > 0])
lose = len([i for i in return_rate if i <= 0])
sum_t = len(return_rate)
print("總獲利次數 : " + str(win) + "次")
print("總虧損次數 : " + str(lose) + "次")
print("總交易次數 : " + str(win + lose) + "次")
print("勝率為 : " + str(round(win / sum_t * 100, 2)) + "%")

cum_return = [0]
for i in range(len(return_rate)):
    cum = round(return_rate[i] + cum_return[i], 2)
    cum_return.append(cum)
print('累積報酬率:', cum_return)
print("該策略平均每次報酬為 : " + str(round(cum_return[-1]/(win + lose), 2)) + "%")

# 年化報酬率(%) = (總報酬率+1)^(1/年數) -1
year_reward = ((((final_money - set_money) / set_money) + 1) ** (1/duration_year) - 1) * 100
print('年化報酬率: ', year_reward, '%')