import math
from datetime import datetime, timedelta
import json
from pprint import pprint
from flask import Flask, render_template, request, flash, send_from_directory, abort, Response
import config
import model_mysql

# backtest
import pandas as pd
import requests
import pandas as pd
from io import StringIO
import os
#visual
import matplotlib.pyplot as plt
import mplfinance as mpf


# sever var
DEBUG = config.DEBUG
PORT = config.PORT
HOST = config.HOST
SECRET_KEY = config.SECRET_KEY

# 建立 flask 實體
app = Flask(__name__)


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
    # form = request.form.to_dict()
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
            'strategy_in_para': '3',
            'strategy_line': 'none_line',
            'strategy_out': 'decrease_out',
            'strategy_out_para': '3',
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
    strategy_in_para = form['strategy_in_para']
    print('strategy_in:', strategy_in)
    print('strategy_in_para:', strategy_in_para)

    # market out: custom para
    strategy_out = form['strategy_out']
    strategy_out_para = form['strategy_out_para']
    print('strategy_out:', strategy_out)
    print('strategy_out_para:', strategy_out_para)

    # transition stop
    strategy_sentiment = form['strategy_sentiment']
    sentiment_para_less = form['sentiment_para_less']
    sentiment_para_more = form['sentiment_para_more']
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

    return render_template('strategy.html')




if __name__ == "__main__":  # 如果以主程式執行
    # initial db
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    # db_mysql.create_tb_all()

    # run sever
    app.run(debug=DEBUG, host=HOST, port=PORT)

    # socketio.run(app, debug=True)



# where (source = 'cnyes' AND category like '%electric_car' OR source = 'cnyes' AND category = 'all') \