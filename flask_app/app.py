import math
from datetime import datetime, timedelta
import json
from pprint import pprint
from flask import Flask, render_template, request, flash, send_from_directory, abort, Response
import config
import model_mysql

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



def fetch_stock_price(range, stock_code):
    duration_dict = {'days': 'daily', 'weeks': 'weekly', 'months': 'monthly', 'years': 'yearly', 'three_years': 'three_yearly', 'five_years': 'five_yearly'}
    if range not in duration_dict.keys():
        print('time_rage error')
    else:
        duration = duration_dict[range]
        date = yesterday_strftime
        sql_stock_price = "SELECT `days`, `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                           FROM `stock_price_{}_{}` \
                           WHERE stock_code = {} \
                           ORDER BY `days` desc;".format(duration, date, stock_code)

        print(sql_stock_price)
        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        result = db_mysql.query_tb_all(sql_stock_price)
        print(result)


        date = [daily_info[0] for daily_info in result]
        # print(date)
        open = [daily_info[4] if daily_info[4] is not None else 0 for daily_info in result]
        low = [daily_info[5] if daily_info[5] is not None else 0 for daily_info in result]
        high = [daily_info[6] if daily_info[6] is not None else 0 for daily_info in result]
        close = [daily_info[7] if daily_info[7] is not None else 0 for daily_info in result]
        volume = [daily_info[8] if daily_info[8] is not None else 0 for daily_info in result]
        start_time = '2016-01-01'
        end_time = date[0]
        # print(result)
        # print(type(start_time))
        range_ = [start_time, end_time]
        # print(range_)
        stock_price = {
            'date': date,
            'open': open,
            'low': low,
            'high': high,
            'close': close,
            'volume': volume,
            'range': range_
        }
        # print(stock_price)
        return stock_price

def fetch_sentiment(range, stock_code, source):
    duration_dict = {'days': 'daily', 'weeks': 'weekly', 'months': 'monthly', 'years': 'yearly',
                     'three_years': 'three_yearly', 'five_years': 'five_yearly'}
    if range not in duration_dict.keys():
        print('time_rage error')
    else:
        duration = duration_dict[range]
        date = yesterday_strftime
        sql_sentiment = "SELECT `days`, `source`, `stock_code`, `stock_name`, `category`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment` \
                         FROM `sentiment_{}_{}` \
                         WHERE stock_code = {} \
                         AND `source` = '{}' \
                         ORDER BY `days` desc;".format(duration, date, stock_code, source)

        print(sql_sentiment)
        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        result = db_mysql.query_tb_all(sql_sentiment)
        print(result)

        date = [daily_info[0] for daily_info in result]
        sum_valence = [daily_info[5] for daily_info in result]
        avg_valence = [daily_info[6] for daily_info in result]
        sum_arousal = [daily_info[7] for daily_info in result]
        avg_arousal = [daily_info[8] for daily_info in result]
        sum_sentiment = [int(daily_info[9]) for daily_info in result]
        sentiment = {
            'date': date,
            'sum_valence': sum_valence,
            'avg_valence': avg_valence,
            'sum_arousal': sum_arousal,
            'avg_arousal': avg_arousal,
            'sum_sentiment': sum_sentiment
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
    date = "20211107"
    sql_social_volume = "SELECT `days`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count` \
                         FROM `social_volume_daily_{}` \
                         WHERE `source` = 'ptt' \
                         ORDER BY `count` DESC, `article_count` DESC \
                         limit 10;".format(date)

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
        date = "20211107"
        sql_social_volume = "SELECT `days`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, (`count` + `article_count`) as total \
                                 FROM `social_volume_daily_{}` \
                                 WHERE `source` = '{}' \
                                 AND `category` = '{}' \
                                 ORDER BY `total` DESC \
                                 limit 10;".format(date, source, category)


    elif duration == 'week':
        date = today_strftime
        sql_social_volume = "SELECT `weeks`, `source`, `category`, `stock_code`, `stock_name`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                             FROM `social_volume_weekly_{}` \
                             WHERE `source` = '{}' \
                             AND `category` = '{}' \
                             GROUP BY `stock_code` \
                             ORDER BY `total` DESC \
                             limit 10;".format(date, source, category)

    elif duration == 'month':
        date = today_strftime
        sql_social_volume = "SELECT `months`, `source`, `category`, `stock_code`, `stock_name`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                             FROM `social_volume_monthly_{}` \
                             WHERE `source` = '{}' \
                             AND `category` = '{}' \
                             GROUP BY `stock_code` \
                             ORDER BY `total` DESC \
                             limit 10;".format(date, source, category)

    elif duration == 'one_year':
        date = today_strftime
        sql_social_volume = "SELECT `years`, `source`, `category`, `stock_code`, `stock_name`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                             FROM `social_volume_yearly_{}` \
                             WHERE `source` = '{}' \
                             AND `category` = '{}' \
                             GROUP BY `stock_code` \
                             ORDER BY `total` DESC \
                             limit 10;".format(date, source, category)

    elif duration == 'three_year':
        date = today_strftime
        sql_social_volume = "SELECT `years`, `source`, `category`, `stock_code`, `stock_name`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                             FROM `social_volume_three_yearly_{}` \
                             WHERE `source` = '{}' \
                             AND `category` = '{}' \
                             GROUP BY `stock_code` \
                             ORDER BY `total` DESC \
                             limit 10;".format(date, source, category)
    else:
        return render_template('error')
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    result = db_mysql.query_tb_all(sql_social_volume)
    print(result)
    stock_name_code = [f'{word_count[4]}, {word_count[3]}' for word_count in result]
    stock_count = [int(word_count[5]) for word_count in result]
    article_count = [int(word_count[6]) for word_count in result]
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
    daily_stock_price = fetch_stock_price('days', 2330)
    # weekly_stock_price = fetch_stock_price('weeks', 2330)
    # monthly_stock_price = fetch_stock_price('months', 2330)
    # yearly_stock_price = fetch_stock_price('years', 2330)
    # three_yearly_stock_price = fetch_stock_price('three_years', 2330)
    # five_yearly_stock_price = fetch_stock_price('five_years', 2330)

    daily_sentiment = fetch_sentiment('days', 0, 'cnyes')
    # weekly_sentiment = fetch_sentiment('weeks', 0, 'cnyes')
    # monthly_sentiment = fetch_sentiment('months', 0, 'cnyes')
    # yearly_sentiment = fetch_sentiment('years', 0, 'cnyes')
    # three_yearly_sentiment = fetch_sentiment('three_years', 0, 'cnyes')
    # five_yearly_sentiment = fetch_sentiment('five_years', 0, 'cnyes')

    return render_template('sentiment.html' , daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment)
                                            # , weekly_stock_price=weekly_stock_price, weekly_sentiment=weekly_sentiment
                                            # , monthly_stock_price=monthly_stock_price, monthly_sentiment=monthly_sentiment
                                            # , yearly_stock_price=yearly_stock_price, yearly_sentiment=yearly_sentiment
                                            # , three_yearly_stock_price=three_yearly_stock_price, three_yearly_sentiment=three_yearly_sentiment
                                            # , five_yearly_stock_price=five_yearly_stock_price, five_yearly_sentiment=five_yearly_sentiment)

@app.route('/single_stock_sentiment', methods=['POST'])
def single_stock_sentiment():
    form = request.form.to_dict()
    pprint(form)
    category = form['category']
    stock_code = form['stock_code']
    source = form['source']
    print(stock_code, source)

    daily_stock_price = fetch_stock_price('days', stock_code)
    weekly_stock_price = fetch_stock_price('weeks', stock_code)
    monthly_stock_price = fetch_stock_price('months', stock_code)
    yearly_stock_price = fetch_stock_price('years', stock_code)
    three_yearly_stock_price = fetch_stock_price('three_years', stock_code)
    five_yearly_stock_price = fetch_stock_price('five_years', stock_code)

    daily_sentiment = fetch_sentiment('days', stock_code, source)
    weekly_sentiment = fetch_sentiment('weeks', stock_code, source)
    monthly_sentiment = fetch_sentiment('months', stock_code, source)
    yearly_sentiment = fetch_sentiment('years', stock_code, source)
    three_yearly_sentiment = fetch_sentiment('three_years', stock_code, source)
    five_yearly_sentiment = fetch_sentiment('five_years', stock_code, source)


    return render_template('sentiment.html', daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment
                           , weekly_stock_price=weekly_stock_price, weekly_sentiment=weekly_sentiment
                           , monthly_stock_price=monthly_stock_price, monthly_sentiment=monthly_sentiment
                           , yearly_stock_price=yearly_stock_price, yearly_sentiment=yearly_sentiment
                           , three_yearly_stock_price=three_yearly_stock_price, three_yearly_sentiment=three_yearly_sentiment
                           , five_yearly_stock_price=five_yearly_stock_price, five_yearly_sentiment=five_yearly_sentiment)


if __name__ == "__main__":  # 如果以主程式執行
    # initial db
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    # db_mysql.create_tb_all()

    # run sever
    app.run(debug=DEBUG, host=HOST, port=PORT)

    # socketio.run(app, debug=True)



# where (source = 'cnyes' AND category like '%electric_car' OR source = 'cnyes' AND category = 'all') \