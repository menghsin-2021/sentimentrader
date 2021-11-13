import os
from datetime import datetime, timedelta
import json
from pprint import pprint
from flask import Flask, render_template, request, flash, send_from_directory, abort, Response, make_response, redirect, url_for
import config
import model_mysql

# backtest
import pandas as pd #引入pandas讀取股價歷史資料CSV檔
import mplfinance as mpf
from sqlalchemy import create_engine
import talib
import numpy as np
from PIL import Image
import io

# user
from hashlib import pbkdf2_hmac
# token
import jwt

from photo_downloader_uploader import upload_file
bucket_name = 'sentimentraderbucket'
object_path = 'backtest'



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

# S3 photo path
S3_PHOTO_PATH = config.S3_PHOTO_PATH

# 建立 flask 實體
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def get_cookie_check():
    try:
        token = request.cookies.get('token')
        print(token)
    except:
        render_template('login.html')
    else:
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], issuer='stock-sentimentrader.com', audience='www.stock-sentimentrader.com', verify_iss=3600)
            user_email = decoded_token['sub']
            print(decoded_token)
            # print(user_email)

        except jwt.exceptions.InvalidSignatureError:
            return Response('Signature verification failed', status=403)
        except jwt.exceptions.ExpiredSignatureError:
            return Response('Signature has expired', status=403)
        except jwt.exceptions.InvalidIssuerError:
            return Response('Invalid issuer', status=403)
        except jwt.exceptions.InvalidAudienceError:
            return Response('Invalid audience', status=403)
        except:
              return False
        else:
            sql_uid = "SELECT `id` as `uid` \
                                   FROM `user` \
                                   WHERE `email` = '{}'".format(user_email)
            db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
            uid = db_mysql.query_tb_one(sql_uid)[0]
            print(uid)
            return uid

def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d')
    yesterday_strftime = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

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
    uid = get_cookie_check()
    print(uid)
    if not isinstance(uid, int):
        return render_template('login.html')
    else:
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
    uid = get_cookie_check()
    print(uid)
    if not isinstance(uid, int):
        return render_template('login.html')
    else:
        return render_template('strategy.html')




@app.route('/send_strategy', methods=['POST'])
def send_strategy():
    uid = get_cookie_check()
    print(uid)
    if not isinstance(uid, int):
        return render_template('login.html')
    else:
        form = request.form.to_dict()
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

        df['avg_valence'] = (df['avg_valence'] + 5) * 10 / 100

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
                timestamp = int(datetime.today().timestamp())
                timestamp_str = str(timestamp)
                filename = f"{stock_code}_{timestamp_str}"
                path = os.path.join("flask_app/static/img/report", filename)
                mpf.plot(df, **kwargs, savefig=path)
                print(filename)
                print(path)
            except:
                print('沒有交易點')
                return render_template('strategy.html')

            else:
                s3_save_filename = filename + '.png'
                s3_save_path = os.path.join('flask_app/static/img/report', s3_save_filename)
                # open file
                pil_image = Image.open(s3_save_path)
                # Save the image to an in-memory file
                in_mem_file = io.BytesIO()
                pil_image.save(in_mem_file, format=pil_image.format)
                in_mem_file.seek(0)
                upload_file(uid, in_mem_file, s3_save_filename, bucket_name, object_path)
                file_path = f"{S3_PHOTO_PATH}/{uid}/{s3_save_filename}"


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

            irr = round((((((final_money - set_money) / set_money) + 1) ** (1 / duration_year)) - 1) * 100, 2)
            print('年化報酬率: ', irr, '%')

            # 策略參數

            strategy_dict = {
                'user_id': uid,
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
                'seed_money': set_money,
                'discount': discount,
                'create_date': today_strftime
            }

            print(strategy_dict)

            # 回測報告
            backtest_report = {
                'user_id': uid,
                'stock_code': stock_code,
                'total_buy_count': total_buy_count,
                'total_sell_count': total_sell_count,
                'total_return_rate': total_return_rate,
                'highest_return': height_return,
                'lowest_return': lowest_return,
                'total_win': total_win,
                'total_lose': total_lose,
                'total_trade': total_trade,
                'win_rate': win_rate,
                'avg_return_rate':  avg_return_rate,
                'irr': irr,
                'file_path': file_path,
                'create_date': today_strftime
            }


            print(backtest_report)

            # strategy_backtest_dict = {
            #     'user_id': uid,
            #     'stock_code': stock_code,
            #     'start_date': start_date,
            #     'end_date': end_date,
            #     'strategy_line': strategy_line,
            #     'strategy_in': strategy_in,
            #     'strategy_in_para': strategy_in_para,
            #     'strategy_out': strategy_out,
            #     'strategy_out_para': strategy_out_para,
            #     'strategy_sentiment': strategy_sentiment,
            #     'source': source,
            #     'sentiment_para_more': sentiment_para_more,
            #     'sentiment_para_less': sentiment_para_less,
            #     'seed_money': set_money,
            #     'discount': discount,
            #     'total_buy_count': total_buy_count,
            #     'total_sell_count': total_sell_count,
            #     'total_return_rate': total_return_rate,
            #     'highest_return': height_return,
            #     'lowest_return': lowest_return,
            #     'total_win': total_win,
            #     'total_lose': total_lose,
            #     'total_trade': total_trade,
            #     'win_rate': win_rate,
            #     'avg_return_rate': avg_return_rate,
            #     'irr': irr,
            #     'file_path': file_path,
            #     'create_date': today_strftime
            # }

            strategy_backtest_tuple = (uid, stock_code, start_date, end_date, strategy_line, strategy_in, strategy_in_para, strategy_out, strategy_out_para,
                                       strategy_sentiment, source, sentiment_para_more, sentiment_para_less,
                                       set_money, discount, total_buy_count, total_sell_count, total_return_rate, height_return, lowest_return,
                                       total_win, total_lose, total_trade, win_rate, avg_return_rate, irr, file_path, today_strftime)



            # sql_insert_strategy = "INSERT INTO `strategy` (`user_id`, `stock_code`, `start_date`, `end_date`, \
            #                                                `strategy_line`, `strategy_in`, `strategy_in_para`, `strategy_out`, `strategy_out_para`, \
            #                                                `strategy_sentiment`, `source`, `sentiment_para_more`, `sentiment_para_less`, `seed_money`, \
            #                                                `discount`, 'create_date') VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            #
            # sql_insert_backtest = "INSERT INTO `backtest` (`user_id`, `stock_code`, `total_buy_count`, `total_sell_count`, \
            #                                                `total_return_rate`, `highest_return`, `lowest_return`, `total_win`, `total_lose` \
            #                                                `total_trade`, `win_rate`, `avg_return_rate`, `irr`, `file_path`, 'create_date') \
            #                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            sql_insert_strategy_backtest = "INSERT INTO `strategy_backtest` (`user_id`, `stock_code`, `start_date`, `end_date`, \
                                                                             `strategy_line`, `strategy_in`, `strategy_in_para`, `strategy_out`, `strategy_out_para`, \
                                                                             `strategy_sentiment`, `source`, `sentiment_para_more`, `sentiment_para_less`, `seed_money`, \
                                                                             `discount`, `total_buy_count`, `total_sell_count`, `total_return_rate`, `highest_return`, \
                                                                             `lowest_return`, `total_win`, `total_lose`, `total_trade`, `win_rate`, `avg_return_rate`, \
                                                                             `irr`, `file_path`, `create_date`) \
                                                                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            # db_mysql.insert_tb(sql_insert_strategy, strategy_tuple)
            # db_mysql.insert_tb(sql_insert_backtest, backtest_tuple)
            db_mysql.insert_tb(sql_insert_strategy_backtest, strategy_backtest_tuple)

            return render_template('backtest.html', backtest_report=backtest_report)



@app.route('/backtest.html', methods=['GET'])
def backtest():
    uid = get_cookie_check()
    print(uid)
    if not isinstance(uid, int):
        return render_template('login.html')
    else:
        sql_social_volume = "SELECT * \
                             FROM `strategy_backtest` \
                             WHERE `user_id` = '{}' \
                             ORDER BY `create_date` DESC \
                             limit 5;".format(uid)

        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        result = db_mysql.query_tb_all(sql_social_volume)
        # pprint(result[0])
        strategy_backtest_dict_list = [{
                'strategy_id': strategy_backtest[0],
                'user_id': strategy_backtest[1],
                'stock_code': strategy_backtest[2],
                'start_date': strategy_backtest[3],
                'end_date': strategy_backtest[4],
                'strategy_line': strategy_backtest[5],
                'strategy_in': strategy_backtest[6],
                'strategy_in_para': strategy_backtest[7],
                'strategy_out': strategy_backtest[8],
                'strategy_out_para': strategy_backtest[9],
                'strategy_sentiment': strategy_backtest[10],
                'source': strategy_backtest[11],
                'sentiment_para_more': strategy_backtest[12],
                'sentiment_para_less': strategy_backtest[13],
                'seed_money': strategy_backtest[14],
                'discount': strategy_backtest[15],
                'total_buy_count': strategy_backtest[16],
                'total_sell_count': strategy_backtest[17],
                'total_return_rate': strategy_backtest[18],
                'highest_return': strategy_backtest[19],
                'lowest_return': strategy_backtest[20],
                'total_win': strategy_backtest[21],
                'total_lose': strategy_backtest[22],
                'total_trade': strategy_backtest[23],
                'win_rate': strategy_backtest[24],
                'avg_return_rate': strategy_backtest[25],
                'irr': strategy_backtest[26],
                'file_path': strategy_backtest[27],
                'create_date': strategy_backtest[28]
            } for strategy_backtest in result]

        strategy_backtest_dict_list_length = len(strategy_backtest_dict_list)
        # pprint(strategy_backtest_dict_list[0])


        return render_template('backtest.html', strategy_backtest_dict_list=strategy_backtest_dict_list, strategy_backtest_dict_list_length=strategy_backtest_dict_list_length)

@app.route('/remove_strategy', methods=['POST'])
def remove_strategy():
    form = request.form.to_dict()
    pprint(form)
    strategy_id = form['remove-strategy']
    print(strategy_id)

    sql_delete_strategy = "DELETE FROM `strategy_backtest` WHERE `id` = '{}'".format(strategy_id)
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    db_mysql.delete_row(sql_delete_strategy)
    print(f"strategy {strategy_id} is deleted")

    resp = make_response(redirect(url_for('backtest')))

    return resp


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

def check_basic_auth_signup(name, email, pwd, con_pwd):
    if name and email and pwd:
        if len(name) <= 255 and len(email) <= 255 and len(pwd) <= 255 and pwd == con_pwd:
            basic_auth = True
        else:
            basic_auth = False
    else:
        basic_auth = False

    return basic_auth

def check_basic_auth_signin(email, pwd):
    if email and pwd:
        if len(email) <= 255 and len(pwd) <= 255:
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

    print(user_signup_request)

    name = user_signup_request['name']
    email = user_signup_request['email']
    pwd = user_signup_request['pwd']
    con_pwd = user_signup_request['con-pwd']

    # db initialize
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')

    # check Basic Auth
    basic_auth = check_basic_auth_signup(name, email, pwd, con_pwd)
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
            sub = email
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
            # signup_api = json.dumps({'data': {'access_token': access_token_str,  # 不能傳 byte 格式
            #                                   'access_expired': access_expired,
            #                                   'user': {
            #                                       'name': name,
            #                                       'email': email,
            #                                   }}}, indent=2, ensure_ascii=False)

            # 回傳token
            signup_user_info = {'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                                              'access_expired': access_expired,
                                              'user': {
                                                  'name': name,
                                                  'email': email,
                                              }}}

            # convert content type from text/html to application/json
            # resp = Response(response=signup_api,
            #                 status=200,
            #                 mimetype="application/json")

            # return render_template('home.html', resp=resp)

            # 對重新導向的 myName.html 做回應
            resp = make_response(redirect(url_for('home')))
            # 回應為set cookie
            resp.set_cookie(key='token', value=signup_user_info['data']['access_token'])
            # 重新導向到 myName.html
            return resp


@app.route('/signin', methods=['POST'])
def signin():
    user_signin_request = request.form.to_dict()
    print(user_signin_request)

    email = user_signin_request['email']
    pwd = user_signin_request['pwd']

    basic_auth = check_basic_auth_signin(email, pwd)

    if not basic_auth:
        return Response('error: wrong format', status=400)
    else:
        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        sql_email = "SELECT `id`, `name`, `email`, `password`, `password_salt` FROM `user` WHERE `email`= %s"
        result = db_mysql.query_tb_one(sql_email, (email,))
        if not result:
            return Response('error: sign in fail', status=403)
        else:
            db_id = result[0]
            db_name = result[1]
            db_email = result[2]
            db_password = result[3]
            db_password_salt = result[4]
            # 處理 password
            password_salt = db_password_salt
            password_hash = generate_hash(pwd, password_salt)
            if db_password != password_hash:
                return Response('error: wrong password', status=403)
            else:
                # 設定 token
                iss = 'stock-sentimentrader.com'
                sub = db_email
                aud = 'www.stock-sentimentrader.com'
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
                # signin_api = json.dumps({'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                #                                   'access_expired': access_expired,
                #                                   'user': {
                #                                       'id': db_id,
                #                                       'name': db_name,
                #                                       'email': db_email,
                #                                   }}}, indent=2, ensure_ascii=False)

                # 回傳token
                signin_user_info = {'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                                             'access_expired': access_expired,
                                             'user': {
                                                 'id': db_id,
                                                 'name': db_name,
                                                 'email': db_email,
                                             }}}

                # # convert content type from text/html to application/json
                # resp = Response(response=signin_api,
                #                 status=200,
                #                 mimetype="application/json")
                # return render_template('home.html', resp=resp)

                resp = make_response(redirect(url_for('home')))
                # 回應為set cookie
                resp.set_cookie(key='token', value=signin_user_info['data']['access_token'])
                # 重新導向到 myName.html

                # set_cookie(key, value='', max_age=None, expires=None, path='/', domain=None, secure=False,
                #            httponly=False, samesite=None)

                return resp



if __name__ == "__main__":  # 如果以主程式執行
    # initial db
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    db_mysql.create_tb_all()

    # run sever
    app.run(debug=DEBUG, host=HOST, port=PORT)

    # socketio.run(app, debug=True)



# where (source = 'cnyes' AND category like '%electric_car' OR source = 'cnyes' AND category = 'all') \