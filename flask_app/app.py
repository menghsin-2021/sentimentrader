import os
from datetime import datetime, timedelta
import json
from pprint import pprint
from flask import Flask, render_template, request, flash, send_from_directory, abort, Response
import config
import model_mysql

# backtest
import pandas as pd #引入pandas讀取股價歷史資料CSV檔
import mplfinance as mpf
from sqlalchemy import create_engine
import talib
import numpy as np


# user
from hashlib import pbkdf2_hmac
# token
import jwt


# sever var
DEBUG = config.DEBUG
PORT = config.PORT
HOST = config.HOST
SECRET_KEY = config.SECRET_KEY

# db var
DBHOST = config.DBHOST
DBUSER = config.DBUSER
DBPASSWORD = config.DBPASSWORD
DBNAME = config.DBNAME
TABLES = "daily_stock_price"
RDSPORT = 3306

# 建立 flask 實體
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def get_today():
    today_strftime = datetime.today().strftime('%Y%m%d')
    yesterday_strftime = (datetime.today() - timedelta(days=1)).strftime('%Y%m%d')

    return today_strftime, yesterday_strftime


def get_day_before(i):
    days_ago_strftime = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') + ' 00:00:00'
    # 2021-11-05 00:00:00 (mysql date)

    return days_ago_strftime


today_strftime, yesterday_strftime = get_today()
seven_days_ago_strftime = get_day_before(7)


def fetch_stock_price(stock_code):
    sql_stock_price = "SELECT `days`, `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `stock_price_view` \
                       WHERE stock_code = {} \
                       ORDER BY `days` desc;".format(stock_code)
    print(sql_stock_price)
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    result = db_mysql.query_tb_all(sql_stock_price)
    print(result)
    return result


def create_stock_price_json(range, result):
    duration_dict = {'days': -1, 'weeks': 7, 'months': 30, 'years': 365, 'three_years': 1095, 'five_years': 1825}
    if range not in duration_dict.keys():
        print('time_rage error')
    else:
        duration = duration_dict[range]
        date = [daily_info[0] for daily_info in result][:duration]
        # print(date)
        open = [daily_info[4] if daily_info[4] is not None else 0 for daily_info in result][:duration]
        low = [daily_info[5] if daily_info[5] is not None else 0 for daily_info in result][:duration]
        high = [daily_info[6] if daily_info[6] is not None else 0 for daily_info in result][:duration]
        close = [daily_info[7] if daily_info[7] is not None else 0 for daily_info in result][:duration]
        volume = [daily_info[8] if daily_info[8] is not None else 0 for daily_info in result][:duration]

        # print(result)
        stock_price = {
            'date': date,
            'open': open,
            'low': low,
            'high': high,
            'close': close,
            'volume': volume
        }
        # print(stock_price)
        return stock_price

def fetch_sentiment(source, stock_code):

        sql_sentiment = "SELECT `days`, `source`, `stock_code`, `stock_name`, `category`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment` \
                         FROM `sentiment_view` \
                         WHERE `source` = '{}' \
                         AND `stock_code` = '{}' \
                         ORDER BY `days` desc;".format(source, stock_code)

        print(sql_sentiment)
        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        result = db_mysql.query_tb_all(sql_sentiment)
        print(result)

        return result

def create_sentiment_json(range, result):
    duration_dict = {'days': -1, 'weeks': 7, 'months': 30, 'years': 365, 'three_years': 1095, 'five_years': 1825}
    if range not in duration_dict.keys():
        print('time_rage error')
    else:
        duration = duration_dict[range]
        date = [daily_info[0] for daily_info in result][:duration]
        chosen_source = [daily_info[1] for daily_info in result][:duration][0]
        chosen_stock_code = [daily_info[2] for daily_info in result][:duration][0]
        chosen_stock_name = [daily_info[3] for daily_info in result][:duration][0]
        sum_valence = [daily_info[5] for daily_info in result][:duration]
        avg_valence = [daily_info[6] for daily_info in result][:duration]
        sum_arousal = [daily_info[7] for daily_info in result][:duration]
        avg_arousal = [daily_info[8] for daily_info in result][:duration]
        sum_sentiment = [int(daily_info[9]) for daily_info in result][:duration]
        avg_valence_now = int((avg_valence[0] + 5) / 10 * 100)
        avg_arousal_now = int((avg_arousal[0] + 5) / 10 * 100)
        sum_sentiment_now = int((sum_sentiment[0] + 5) / 100 * 100)
        avg_valence_angular = int(avg_valence_now / 100 * 180)

        sentiment = {
            'date': date,
            'sum_valence': sum_valence,
            'avg_valence': avg_valence,
            'sum_arousal': sum_arousal,
            'avg_arousal': avg_arousal,
            'sum_sentiment': sum_sentiment,
            'avg_valence_now': avg_valence_now,
            'avg_valence_angular': avg_valence_angular,
            'avg_arousal_now': avg_arousal_now,
            'sum_sentiment_now': sum_sentiment_now,
            'chosen_source': chosen_source,
            'chosen_stock_code': chosen_stock_code,
            'chosen_stock_name': chosen_stock_name
        }

        return sentiment

@app.route('/', methods=['GET'])
@app.route('/login.html', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/home.html', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/social_volume.html', methods=['GET'])
def social_volume():
    # user count
    sql_social_volume = "SELECT *, (`count` + `article_count`) as total \
                         FROM `social_volume_daily` \
                         WHERE `source` = 'ptt' \
                         ORDER BY `total` DESC \
                         limit 10;"

    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    result = db_mysql.query_tb_all(sql_social_volume)
    pprint(result)

    stock_name_code = [f'{word_count[4]}, {word_count[3]}' for word_count in result]
    stock_count = [int(word_count[5]) for word_count in result]
    article_count = [int(word_count[6]) for word_count in result]
    social_volume_rank = json.dumps({
        'stock_name_code': stock_name_code,
        'stock_count': stock_count,
        'article_count': article_count,
        'title': '個股媒體熱度排名(當日)'
    }, indent=2, ensure_ascii=False)
    print(social_volume_rank)
    return render_template('social_volume.html', social_volume_rank=social_volume_rank)


@app.route('/social_volume_rank', methods=['POST'])
def social_volume_rank():
    form = request.form.to_dict()
    pprint(form)
    category = form['category']
    duration = form['duration']
    source = form['source']

    if duration == 'day':
        if category == 'electric' or category == 'electric_car':
            category_1 = 'electric_electric_car'
            sql_social_volume = "SELECT `stock_name`, `stock_code`, `count`, `article_count`, (`count` + `article_count`) as total \
                                     FROM `social_volume_daily` \
                                     WHERE `source` = '{}' \
                                     AND `category` = '{}' \
                                     OR `category` = '{}' \
                                     ORDER BY `total` DESC \
                                     limit 10;".format(source, category, category_1)
        else:
            sql_social_volume = "SELECT `stock_name`, `stock_code`, `count`, `article_count`, (`count` + `article_count`) as total \
                                 FROM `social_volume_daily` \
                                 WHERE `source` = '{}' \
                                 AND `category` = '{}' \
                                 ORDER BY `total` DESC \
                                 limit 10;".format(source, category)

    else:
        if category == 'electric' or category == 'electric_car':
            category_1 = 'electric_electric_car'
            sql_social_volume = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                         FROM `social_volume_{}` \
                                         WHERE `source` = '{}' \
                                         AND `category` = '{}' \
                                         OR `category` = '{}' \
                                         GROUP BY `stock_code` \
                                         ORDER BY `total` DESC \
                                         limit 10;".format(duration, source, category, category_1)
        else:
            sql_social_volume = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                 FROM `social_volume_{}` \
                                 WHERE `source` = '{}' \
                                 AND `category` = '{}' \
                                 GROUP BY `stock_code` \
                                 ORDER BY `total` DESC \
                                 limit 10;".format(duration, source, category)


    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    result = db_mysql.query_tb_all(sql_social_volume)
    print(result)
    stock_name_code = [f'{word_count[0]}, {word_count[1]}' for word_count in result]
    stock_count = [int(word_count[2]) for word_count in result]
    article_count = [int(word_count[3]) for word_count in result]
    social_volume_rank = json.dumps({
        'stock_name_code': stock_name_code,
        'stock_count': stock_count,
        'article_count': article_count,
        'title': f"{category}, {duration}, {source} 個股媒體熱度排名"
    }, indent=2, ensure_ascii=False)
    print(social_volume_rank)
    return render_template('social_volume.html', social_volume_rank=social_volume_rank)


@app.route('/sentiment.html')
def sentiment():
    result_stock_price = fetch_stock_price(2330)

    daily_stock_price = create_stock_price_json('days', result_stock_price)
    weekly_stock_price = create_stock_price_json('weeks', result_stock_price)
    monthly_stock_price = create_stock_price_json('months', result_stock_price)
    yearly_stock_price = create_stock_price_json('years', result_stock_price)
    three_yearly_stock_price = create_stock_price_json('three_years', result_stock_price)
    five_yearly_stock_price = create_stock_price_json('five_years', result_stock_price)

    result_sentiment = fetch_sentiment('cnyes', 2330)
    daily_sentiment = create_sentiment_json('days', result_sentiment)
    weekly_sentiment = create_sentiment_json('weeks', result_sentiment)
    monthly_sentiment = create_sentiment_json('months', result_sentiment)
    yearly_sentiment = create_sentiment_json('years', result_sentiment)
    three_yearly_sentiment = create_sentiment_json('three_years', result_sentiment)
    five_yearly_sentiment = create_sentiment_json('five_years', result_sentiment)

    return render_template('sentiment.html' , daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment
                                            , weekly_stock_price=weekly_stock_price, weekly_sentiment=weekly_sentiment
                                            , monthly_stock_price=monthly_stock_price, monthly_sentiment=monthly_sentiment
                                            , yearly_stock_price=yearly_stock_price, yearly_sentiment=yearly_sentiment
                                            , three_yearly_stock_price=three_yearly_stock_price, three_yearly_sentiment=three_yearly_sentiment
                                            , five_yearly_stock_price=five_yearly_stock_price, five_yearly_sentiment=five_yearly_sentiment)

@app.route('/single_stock_sentiment', methods=['POST'])
def single_stock_sentiment():
    form = request.form.to_dict()
    pprint(form)
    category = form['category']
    stock_code = form['stock_code']
    source = form['source']
    print(stock_code, source)

    result_stock_price = fetch_stock_price(stock_code)

    daily_stock_price = create_stock_price_json('days', result_stock_price)
    weekly_stock_price = create_stock_price_json('weeks', result_stock_price)
    monthly_stock_price = create_stock_price_json('months', result_stock_price)
    yearly_stock_price = create_stock_price_json('years', result_stock_price)
    three_yearly_stock_price = create_stock_price_json('three_years', result_stock_price)
    five_yearly_stock_price = create_stock_price_json('five_years', result_stock_price)

    result_sentiment = fetch_sentiment(source, stock_code)
    daily_sentiment = create_sentiment_json('days', result_sentiment)
    weekly_sentiment = create_sentiment_json('weeks', result_sentiment)
    monthly_sentiment = create_sentiment_json('months', result_sentiment)
    yearly_sentiment = create_sentiment_json('years', result_sentiment)
    three_yearly_sentiment = create_sentiment_json('three_years', result_sentiment)
    five_yearly_sentiment = create_sentiment_json('five_years', result_sentiment)


    return render_template('sentiment.html', daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment
                           , weekly_stock_price=weekly_stock_price, weekly_sentiment=weekly_sentiment
                           , monthly_stock_price=monthly_stock_price, monthly_sentiment=monthly_sentiment
                           , yearly_stock_price=yearly_stock_price, yearly_sentiment=yearly_sentiment
                           , three_yearly_stock_price=three_yearly_stock_price, three_yearly_sentiment=three_yearly_sentiment
                           , five_yearly_stock_price=five_yearly_stock_price, five_yearly_sentiment=five_yearly_sentiment)


@app.route('/strategy.html', methods=['GET'])
def strategy():
    return render_template('strategy.html')


@app.route('/send_strategy', methods=['POST'])
def send_strategy():
    form = request.form.to_dict()
    # form = {'category': 'sail',
    #         'discount': '40',
    #         'end_date': '2020-11-10',
    #         'money': '500',
    #         'sentiment_para_less': '40',
    #         'sentiment_para_more': '60',
    #         'source': 'ptt',
    #         'start_date': '2018-01-01',
    #         'stock_code': '2603',
    #         'strategy_in': 'increase_in',
    #         'strategy_in_para': '3',
    #         'strategy_line': 'none_line',
    #         'strategy_out': 'decrease_out',
    #         'strategy_out_para': '3',
    #         'strategy_sentiment': 'daily_sentiment_pass'}
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
    try:
        strategy_in_para = float(form['strategy_in_para'])
    except:
        strategy_in_para = 1
    print('strategy_in:', strategy_in)
    print('strategy_in_para:', strategy_in_para)
    # market out: custom para
    strategy_out = form['strategy_out']
    try:
        strategy_out_para = float(form['strategy_out_para'])
    except:
        strategy_out_para = 1
    print('strategy_out:', strategy_out)
    print('strategy_out_para:', strategy_out_para)
    # transition stop
    strategy_sentiment = form['strategy_sentiment']
    try:
        sentiment_para_less = float(form['sentiment_para_less'])
        sentiment_para_more = float(form['sentiment_para_more'])
    except:
        sentiment_para_more = 60
        sentiment_para_less = 40
    print('strategy_sentiment:', strategy_sentiment)
    print('sentiment_para_less:', sentiment_para_less)
    print('sentiment_para_more:', sentiment_para_more)
    # print((float(sentiment_para_more) / 100 * 10 - 5))
    # print((float(sentiment_para_less) / 100 * 10 - 5))
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
                                                 ORDER BY `Date`".format(stock_code, start_date_datetime,
                                                                         end_date_datetime))

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
                if df['avg_valence'][i] < (float(sentiment_para_more) / 100 * 10 - 5) and df['avg_valence'][i] > (
                        float(sentiment_para_less) / 100 * 10 - 5):
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

            print('money', money)
            df["buy"] = buy
            df["sell"] = sell

        # KD + sentiment to negative
        elif strategy_sentiment == 'to_negative_pass':
            buy = []
            sell = []
            buy_count = 0
            for i in range(len(df)):
                if i > 0:
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

                elif df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
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
                if i > 0:
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

                elif df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
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
                        if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][
                            i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                            buy.append(1)
                            sell.append(0)
                            buy_count += 1
                            money -= df["Close"][i]
                        elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                                df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
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
                        if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][
                            i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                            buy.append(1)
                            sell.append(0)
                            buy_count += 1
                            money -= df["Close"][i]
                        elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                                df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
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
                    if i > 0:
                        if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][
                            i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                            buy.append(1)
                            sell.append(0)
                            buy_count += 1
                            money -= df["Close"][i]
                        elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                                df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                            sell.append(-1)
                            buy.append(0)
                            buy_count -= 1
                            money += df["Close"][i]
                        else:
                            buy.append(0)
                            sell.append(0)
                    elif df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
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
                    if i > 0:
                        if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][
                            i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                            buy.append(1)
                            sell.append(0)
                            buy_count += 1
                            money -= df["Close"][i]
                        elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][i - 1] and \
                                df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                            sell.append(-1)
                            buy.append(0)
                            buy_count -= 1
                            money += df["Close"][i]
                        else:
                            buy.append(0)
                            sell.append(0)
                    elif df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
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
                        if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                            i - 1] and \
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
                        if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                            i - 1] and \
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
                    if i > 0:
                        if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                            i - 1] and \
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
                    elif df['avg_valence'][i] < 0 and df['avg_valence'][i - 1] > 0:
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
                    if i > 0:
                        if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                            i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
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

                    elif df['avg_valence'][i] > 0 and df['avg_valence'][i - 1] < 0:
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

    if len(buy_mark) > 0 and len(sell_mark) > 0:
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
                        mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'), ]
    else:
        add_plot = None

    if add_plot == None:
        print('沒有交易點')
        return render_template('strategy.html')
    else:
        try:
            df.index = pd.DatetimeIndex(df.index)
            stock_id = "{}.TW".format(stock_code)
            mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
            s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, rc={'font.size': 14})
            kwargs = dict(type='candle', volume=True, figsize=(20, 10), title=stock_id, style=s, addplot=add_plot)
            filename = stock_code + '_' + datetime.today().strftime('%Y-%m-%d')
            path = os.path.join("flask_app/static/img/report", filename)
            mpf.plot(df, **kwargs, savefig=path)
            print(filename)
            print(path)
        except:
            print('沒有交易點')
            return render_template('strategy.html')

        # 計算買進和賣出次數
        buy1 = df.loc[df["buy"] == 1]
        sell1 = df.loc[df["sell"] == -1]
        print(buy1)
        print(sell1)

        total_buy_count = len(buy1)
        total_sell_count = len(sell1)
        print("買進次數 : " + str(total_buy_count) + "次")
        print("賣出次數 : " + str(total_sell_count) + "次")

        sell1 = sell1.append(df[-1:])
        print(sell1.tail())

        money = set_money
        print('資金: ', money)
        if len(sell1) >= 0:
            for i in range(len(sell1) - 1):
                money = money - buy1["Close"][i] + sell1['Close'][i] - ((buy1["Close"][i] + sell1["Close"][i]) * 0.001425 * discount / 100)

            final_money = money + ((len(buy1) - len(sell1)) * sell1["Close"][-1])
        else:
            final_money = money

        print('最後所得金額: ', final_money)
        print('淨收益: ', final_money - set_money)
        total_return_rate = round((final_money - set_money) / set_money * 100, 2)
        print('總報酬率(淨收益) = ', total_return_rate, '%')

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

        height_return = return_all[0]
        lowest_return = return_all[-1]

        print("該策略最高報酬為 : " + str(height_return) + " %")
        print("該策略最低報酬為 : " + str(lowest_return) + " %")


        total_win = len([i for i in return_rate if i > 0])
        total_lose = len([i for i in return_rate if i <= 0])
        total_trade = total_win + total_lose
        sum_t = len(return_rate)
        win_rate = round(total_win / sum_t * 100, 2)
        print("總獲利次數 : " + str(total_win) + "次")
        print("總虧損次數 : " + str(total_lose) + "次")
        print("總交易次數 : " + str(total_trade) + "次")
        print("勝率為 : " + str(win_rate) + "%")

        cum_return = [0]
        for i in range(len(return_rate)):
            cum = round(return_rate[i] + cum_return[i], 2)
            cum_return.append(cum)
        print('累積報酬率:', cum_return)
        avg_return_rate = round(cum_return[-1] / (total_win + total_lose), 2)
        print("該策略平均每次報酬為 : " + str(avg_return_rate) + "%")

        # 年化報酬率(%) = (總報酬率+1)^(1/年數) -1
        irr = round(((((final_money - set_money) / set_money) + 1) ** (1 / duration_year) - 1) * 100, 2)
        print('年化報酬率: ', irr, '%')

        # 策略參數

        strategy_dict = {
            'uid': 'test@gmail.com',
            'stock_code': stock_code,
            'start_date': start_date,
            'end_date': end_date,
            'strategy_line': strategy_line,
            'strategy_in': strategy_in,
            'strategy_in_para': strategy_in_para,
            'strategy_out': strategy_out,
            'strategy_out_para': strategy_out_para,
            'strategy_sentiment': strategy_sentiment,
            'source': source,
            'sentiment_para_more': sentiment_para_more,
            'sentiment_para_less': sentiment_para_less,
            'money': set_money,
            'discount': discount,
        }

        print(strategy_dict)

        # 回測報告
        backtest_report = {
            'total_buy_count': total_buy_count,
            'total_sell_count': total_sell_count,
            'total_return_rate': total_return_rate,
            'height_return': height_return,
            'lowest_return': lowest_return,
            'total_win': total_win,
            'total_lose': total_lose,
            'total_trade': total_trade,
            'win_rate': win_rate,
            'avg_return_rate':  avg_return_rate,
            'irr': irr,
            'filename': filename,
        }

        print(backtest_report)

        return render_template('backtest.html', filename=filename, backtest_report=backtest_report)



@app.route('/backtest.html', methods=['GET'])
def backtest():
    return render_template('backtest.html', filename="2317_2021-11-11")




# user api
# utils function
def generate_salt():
    salt = os.urandom(16)
    return salt.hex()  # 轉換16進制

def generate_hash(plain_password, password_salt):
    # 基於密碼的金鑰派生函式2以HMAC為偽隨機函式。
    password_hash = pbkdf2_hmac(
        "sha256",  # hash name  返回一個sha256物件；把字串轉換為位元組形式；
        b"%b" % bytes(plain_password, "utf-8"),  # password 二進制數據  原本: b"%b" % bytes(plain_password, "utf-8")
        b"%b" % bytes(password_salt, "utf-8"),  # salt 二進制數據  原本: b"%b" % bytes(password_salt, "utf-8")
        10000,  # iterations
    )
    return password_hash.hex()  # 轉換16進制

def b_type_to_str(b_type):
    if type(b_type) is bytes:
        b_type = str(b_type)[2:-1]
    else:
        b_type = str(b_type)
    return b_type

def check_basic_auth(name, email, pwd, con_pwd):
    if name and email and pwd:
        if len(name) <= 255 and len(email) <= 255 and len(pwd) <= 255 and pwd == con_pwd:
            basic_auth = True
        else:
            basic_auth = False
    else:
        basic_auth = False

    return basic_auth

def set_token(iss, sub, aud, iat, nbf, exp, jti):
    payload = {
        'iss': iss,  # (Issuer) Token 的發行者
        'sub': sub,  # (Subject) 也就是使用該 Token 的使用者
        'aud': aud,  # Token 的接收者，也就是後端伺服器
        'exp': exp,  # (Expiration Time) Token 的過期時間 (must use UTC time) 應該 iat + 秒數
        'nbf': nbf,  # (Not Before) Token 的生效時間
        'iat': iat,  # (Issued At) Token 的發行時間
        'jti': jti,  # (JWT ID) Token 的 ID
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return access_token


# sign-up API
@app.route('/signup', methods=['POST'])
def signup():
    # get request data
    user_signup_request = request.form.to_dict()
    # force(bool) – Ignore the mimetype and always try to parse JSON.
    # silent(bool) – Silence parsing errors and return None instead
    # cache (bool) – Store the parsed JSON to return for subsequent calls.

    print(user_signup_request)

    name = user_signup_request['name']
    email = user_signup_request['email']
    pwd = user_signup_request['pwd']
    con_pwd = user_signup_request['con-pwd']

    # db initialize
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')

    # check Basic Auth
    basic_auth = check_basic_auth(name, email, pwd, con_pwd)
    if not basic_auth:
        return Response('error: wrong format or miss something', status=400)

    else:
        # 搜尋是否有相同的email
        sql_email = "SELECT `id` FROM `user` WHERE `email`= %s"
        result_email = db_mysql.query_tb_one(sql_email, (email,))

        if result_email:
            db_mysql.close_db()
            return Response('error: email is exist', status=403)

        else:
            # 處理 password
            password_salt = generate_salt()
            password_hash = generate_hash(pwd, password_salt)

            # 設定 token
            iss = 'stock-sentimentrader.com'
            sub = name
            aud = 'www.stock-sentimentrader.com'
            iat = datetime.utcnow()
            nbf = datetime.utcnow()
            exp = iat + timedelta(seconds=3600)
            jti = email

            access_token = set_token(iss, sub, aud, iat, nbf, exp, jti)
            access_token_str = b_type_to_str(access_token)
            access_expired = int(exp.timestamp()-iat.timestamp())
            # 其中 secret 就是密鑰（不可外洩，否則人人都能夠做出一樣的 JWT)
            # 而 HS256 則是簽章的算法，也就是預設的 HMAC SHA526。
            # 目前 PyJWT 支援 RS256 與 HS256 2 種簽章算法

            # 插入資料庫
            sql = "INSERT INTO `user` (`name`, `email`, `password`, `password_salt`, `access_token`, `access_expired`) VALUES (%s, %s, %s, %s, %s, %s)"
            db_mysql.insert_tb(sql, (name, email, password_hash, password_salt, access_token, access_expired))
            flash('signup success')

            # 回傳 json
            signup_api = json.dumps({'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                                              'access_expired': access_expired,
                                              'user': {
                                                  'id': id,
                                                  'name': name,
                                                  'email': email,
                                              }}}, indent=2, ensure_ascii=False)

            # convert content type from text/html to application/json
            resp = Response(response=signup_api,
                            status=200,
                            mimetype="application/json")

            return resp



@app.route('/signin', methods=['POST'])
def signin():
    user_signin_request = request.get_json(force=False, silent=False, cache=True)
    provider = user_signin_request['provider']
    if not user_signin_request:
        return Response('error: miss email or password', status=400)

    elif provider == 'native':
        email = user_signin_request['email']
        password = user_signin_request['password']
        basic_auth = check_basic_auth(provider, email, password)
        # Basic Auth
        if not basic_auth:
            return Response('error: wrong format', status=400)
        else:
            db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
            sql_email = "SELECT `id`, `provider`, `name`, `email`, `password`, `password_salt`, `picture` FROM `user` WHERE `email`= %s"
            result = db_mysql.query_tb_one(sql_email, (email,))
            if not result:
                return Response('error: sign in fail', status=403)
            else:
                db_id = result[0]
                db_provider = result[1]
                db_name = result[2]
                db_email = result[3]
                db_password = result[4]
                db_password_salt = result[5]
                db_picture = result[6]

                # 處理 password
                password_salt = db_password_salt
                password_hash = generate_hash(password, password_salt)
                if db_password != password_hash:
                    return Response('error: wrong password', status=403)
                else:
                    # 設定 token
                    iss = 'appworks.com'
                    sub = db_name
                    aud = 'www.stylish.com'
                    iat = datetime.utcnow()
                    nbf = datetime.utcnow()
                    exp = iat + timedelta(seconds=3600)
                    jti = email

                    access_token = set_token(iss, sub, aud, iat, nbf, exp, jti)
                    access_token_str = b_type_to_str(access_token)
                    access_expired = int(exp.timestamp() - iat.timestamp())
                    # 其中 secret 就是密鑰（不可外洩，否則人人都能夠做出一樣的 JWT)
                    # 而 HS256 則是簽章的算法，也就是預設的 HMAC SHA526。
                    # 目前 PyJWT 支援 RS256 與 HS256 2 種簽章算法
                    # 更新資料庫token
                    sql_update = "UPDATE `user` SET `access_token`=%s, `access_expired`=%s WHERE `email`=%s"
                    db_mysql.update_tb(sql_update, (access_token, access_expired, email))
                    db_mysql.close_db()
                    flash('signin success')
                    # 回傳 json
                    signup_api = json.dumps({'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                                                      'access_expired': access_expired,
                                                      'user': {
                                                          'id': db_id,
                                                          'provider': db_provider,
                                                          'name': db_name,
                                                          'email': db_email,
                                                          'picture': db_picture,
                                                      }}}, indent=2, ensure_ascii=False)
                    # convert content type from text/html to application/json
                    resp = Response(response=signup_api,
                                    status=200,
                                    mimetype="application/json")
                    return resp


    # elif provider == 'facebook':
    #     fb_access_token = user_signin_request['access_token']
    #     if not fb_access_token:
    #         flash('error: miss token')
    #         return Response(status=400) and 'error: miss token'
    #
    #     else:
    #         if len(fb_access_token) > 255:
    #             flash('error: wrong format')
    #             return Response('error: wrong format', status=400)
    #
    #         else:
    #             r_token = requests.get("https://graph.facebook.com/debug_token?input_token={}&access_token={}".format(fb_access_token, APPTOKEN))  # 網址來自圖形API測試工具的 cURL，token 可用 測試用戶產生存取權杖
    #             if r_token.status_code != requests.codes.ok:
    #                 print(r_token.status_code)  # 如果文章被刪會跳 404 (或 ip 被 ban)
    #                 return Response('error: no reaction', status=400)
    #
    #             else:
    #                 token_information = r_token.json()
    #                 print(token_information)
    #                 try:
    #                     valid = token_information['data']['is_valid']
    #
    #                 except:
    #                     return Response('Session has expired', status=400)
    #
    #                 else:
    #                     fb_access_expired = token_information['data']['expires_at'] - int(datetime.utcnow().timestamp())  #fb_access_expired
    #                     token_user_ID = token_information['data']['user_id']
    #                     fbID = token_user_ID  # fbID
    #
    #                     # 檢查用戶資料
    #                     r_person = requests.get(
    #                         "https://graph.facebook.com/v11.0/me?fields=id%2Cname%2Cemail%2Cpicture&access_token={}".format(
    #                             fb_access_token))  # 網址來自圖形API測試工具的 cURL，token 可用 測試用戶產生存取權杖
    #                     if r_person.status_code != requests.codes.ok:
    #                         pprint(r_person.status_code)  # 如果文章被刪會跳 404 (或 ip 被 ban)
    #                         return Response('error: no reaction', status=400)
    #
    #                     try:
    #                         personal_information = r_person.json()
    #                         name = personal_information['name']  # name
    #                         email = personal_information['email']  # email
    #                         picture = personal_information['picture']['data']['url']  # picture
    #                         password = 'facebooklogin'  # password
    #                         password_salt = 'facebooklogin'  # password_salt
    #
    #                     except:
    #                         return Response('error: no email information', status=400)
    #
    #                     else:
    #                         # 檢查 FB token OK 跟取得用戶資料之後 就先做一個 token
    #                         # 設定 token
    #                         iss = 'appworks.com'
    #                         sub = name
    #                         aud = 'www.stylish.com'
    #                         iat = datetime.utcnow()
    #                         nbf = datetime.utcnow()
    #                         exp = iat + timedelta(seconds=3600)
    #                         jti = email
    #
    #                         access_token = set_token(iss, sub, aud, iat, nbf, exp, jti)
    #                         access_token_str = b_type_to_str(access_token)
    #                         access_expired = int(exp.timestamp() - iat.timestamp())
    #
    #                         # 檢查資料庫是否已經有相同的使用者 (有了就更新 token 就好)
    #                         sql_fbID = "SELECT `fbID` FROM `user` WHERE `fbID`= %s"
    #                         db_mysql = model_mysql.DbWrapperMysql('stylish')
    #                         try:
    #                             result = db_mysql.query_tb_all(sql_fbID, (fbID,))
    #                             fbID = result[0]
    #
    #                         except:
    #                             # 如果沒有就插入資料庫
    #                             sql_fb_user_insert = "INSERT INTO `user` (`name`, `email`, `password`, `password_salt`, `provider`,`access_token`, `access_expired`, `picture`, `fbID`, `fb_access_token`, `fb_access_expired`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    #                             db_mysql.insert_tb(sql_fb_user_insert, (name, email, password, password_salt, provider, access_token, access_expired, picture, fbID, fb_access_token, fb_access_expired))
    #                             db_mysql.close_db()
    #                             flash('signin success')
    #
    #                         else:
    #                             # 更新資料庫token
    #                             sql_update = "UPDATE `user` SET `access_token`=%s, `access_expired`=%s, `fb_access_token`=%s, `fb_access_expired`=%s WHERE `fbID`=%s"
    #                             db_mysql.update_tb(sql_update, (access_token, access_expired, fb_access_token, fb_access_expired, fbID))
    #                             db_mysql.close_db()
    #                             flash('signin success')
    #
    #                         # 回傳 json
    #                         signin_api = json.dumps({'data': {'access_token': access_token_str,
    #                                                           'access_expired': access_expired,
    #                                                           'user': {
    #                                                               'id': fbID,
    #                                                               'provider': provider,
    #                                                               'name': name,
    #                                                               'email': email,
    #                                                               'picture': picture,
    #                                                           }}}, indent=2, ensure_ascii=False)
    #
    #                         # convert content type from text/html to application/json
    #                         resp = Response(response=signin_api,
    #                                         status=200,
    #                                         mimetype="application/json")
    #                         return resp

    else:
        flash('error: unknown provider')
        return Response('error: unknown provider', status=400)



# @app.route('/profile', methods=['GET'])
# def profile():
#     header = request.headers  # 取 header
#     if 'Authorization' not in header:  # 判斷有沒有 Authorization key
#         return Response('invalid_request', status=400)
#
#     else:
#         authorization = header['Authorization']
#         if 'Bearer' not in authorization or len(authorization) == 0:
#             return Response('invalid_request', status=400)
#
#         else:
#             request_token = header['Authorization'].replace('Bearer ', '')  # 判斷有沒有 token value 而且要有 Bearer
#             try:
#                 # 解 token 判斷來源和期限
#                 decoded_token = jwt.decode(request_token, SECRET_KEY, algorithms=["HS256"], issuer='appworks.com', audience='www.stylish.com' or 'www.facebook.com')
#                 print(decoded_token)
#
#             except jwt.exceptions.InvalidSignatureError:
#                 return Response('Signature verification failed', status=403)
#
#             except jwt.exceptions.ExpiredSignatureError:
#                 return Response('Signature has expired', status=403)
#
#             except jwt.exceptions.InvalidIssuerError:
#                 return Response('Invalid issuer', status=403)
#
#             except jwt.exceptions.InvalidAudienceError:
#                 return Response('Invalid audience', status=403)
#
#             except:
#                 return Response('wrong token', status=403)
#
#             else:
#                 flash('valid success')
#                 try:
#                     db_mysql = model_mysql.DbWrapperMysql('stylish')
#                     sql_profile = "SELECT `provider`, `name`, `email`, `picture` FROM `user` WHERE `access_token`= %s"
#                     result = db_mysql.query_tb_one(sql_profile, (request_token,))
#
#                 except:
#                     return Response('unknown token', status=400)
#
#                 else:
#                     provider = result[0]
#                     name = result[1]
#                     email = result[2]
#                     picture = result[3]
#
#                     profile_api = json.dumps({'data': {
#                                                         'provider': provider,
#                                                         'name': name,
#                                                         'email': email,
#                                                         'picture': picture,
#                                                       }}, indent=2, ensure_ascii=False)
#
#                     # convert content type from text/html to application/json
#                     resp = Response(response=profile_api,
#                                     status=200,
#                                     mimetype="application/json")
#                     return resp



@app.route('/welcome')
def welcome():
    # get cookie
    name = request.cookies.get('user')
    # 如果可以拿到 cookie 就顯示
    if name:
        return '<h1>welcome ' + name + '</h1>'
    # 不能就回首頁
    else:
        return render_template('user.html')



if __name__ == "__main__":  # 如果以主程式執行
    # initial db
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    # db_mysql.create_tb_all()

    # run sever
    app.run(debug=DEBUG, host=HOST, port=PORT)

    # socketio.run(app, debug=True)



# where (source = 'cnyes' AND category like '%electric_car' OR source = 'cnyes' AND category = 'all') \