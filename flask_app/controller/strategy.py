import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
import pandas as pd
import mplfinance as mpf
from sqlalchemy import create_engine
import talib
import numpy as np
from PIL import Image
import io
from datetime import datetime, timedelta
import json

import config
from model import model_mysql
from model import model_mysql_query
from utils import get_cookie_check, get_today_yesterday, get_day_before, upload_file, GetName

# db var
DBHOST = config.DBHOST
DBUSER = config.DBUSER
DBPASSWORD = config.DBPASSWORD
DBNAME = config.DBNAME

BUCKET_NAME = config.BUCKET_NAME
OBJECT_PATH = config.OBJECT_PATH

# S3 photo path
S3_PHOTO_PATH = config.S3_PHOTO_PATH

# basedir
BASEDIR = config.BASEDIR

# Blueprint
strategy = Blueprint('strategy', __name__, static_folder='static', template_folder='templates')


@strategy.route('/strategy.html', methods=['GET'])
def strategy_page():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')

    else:
        sql_sample_strategy = model_mysql_query.sql_sample_strategy
        db_mysql = model_mysql.DbWrapperMysqlDict('sentimentrader')
        sample_strategy_form = db_mysql.query_tb_all(sql_sample_strategy)
        sample_strategy_form_length = int(len(sample_strategy_form))
        # print(sample_strategy_form)
        get_name = GetName()

        def add_key(sample_strategy):
            sample_strategy['category_name'] = get_name.category(sample_strategy['category'])
            sample_strategy['strategy_line_name'] = get_name.strategy_line(sample_strategy['strategy_line'])
            sample_strategy['strategy_in_name'] = get_name.strategy_in(sample_strategy['strategy_in'])
            sample_strategy['strategy_out_name'] = get_name.strategy_out(sample_strategy['strategy_out'])
            sample_strategy['strategy_sentiment_name'] = get_name.strategy_sentiment(sample_strategy['strategy_sentiment'])
            sample_strategy['source_name'] = get_name.source(sample_strategy['source'])
            return sample_strategy

        sample_strategy_form = [add_key(sample_strategy) for sample_strategy in sample_strategy_form]

        return render_template('strategy.html', sample_strategy_form=sample_strategy_form, sample_strategy_form_length=sample_strategy_form_length)



@strategy.route('/api/1.0/send_strategy', methods=['POST'])
def send_strategy():
    uid = get_cookie_check()
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')
    else:
        try:
            form = request.form.to_dict()
            # category and stock_code
            category = form['category']
            stock_code = form['stock_code']

            # duration
            start_date = form['start_date']
            end_date = form['end_date']
            start_date_datetime = datetime.fromisoformat(start_date)
            end_date_datetime = datetime.fromisoformat(end_date)

            if end_date_datetime <= start_date_datetime:
                flash("開始日期須小於結束日期", 'error')
                return redirect(url_for('strategy.strategy_page'))

            # KD, MACD, or custom
            strategy_line = form['strategy_line']

            # market in: custom para
            strategy_in = form['strategy_in']
            try:
                strategy_in_para = float(form['strategy_in_para'])
            except:
                strategy_in_para = 1

            # market out: custom para
            strategy_out = form['strategy_out']
            try:
                strategy_out_para = float(form['strategy_out_para'])
            except:
                default_strategy_out_para = 1
                strategy_out_para = default_strategy_out_para

            # transition stop
            strategy_sentiment = form['strategy_sentiment']
            try:
                sentiment_para_less = float(form['sentiment_para_less'])
                sentiment_para_more = float(form['sentiment_para_more'])
            except:
                default_sentiment_para_more = 60
                default_sentiment_para_less = 40
                sentiment_para_more = default_sentiment_para_more
                sentiment_para_less = default_sentiment_para_less

            # your fee discount
            source = form['source']
            # your fund
            set_money = int(form['money'])
            # your fee discount
            discount = float(form['discount'])
            duration_day = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date))
            year_days = 365
            duration_year = round(duration_day.days / year_days, 2)

        except:
            flash("數值錯誤", 'error')
            return redirect(url_for('strategy.strategy_page'))

        else:
            engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                                   .format(user=DBUSER,
                                           pw=DBPASSWORD,
                                           db=DBNAME,
                                           host=DBHOST))

            connection = engine.connect()

            # set date
            resoverall_stock_price = connection.execute(model_mysql_query.sql_strategy_stock_price(stock_code, start_date_datetime, end_date_datetime))

            # fetch stock price
            df1 = pd.DataFrame(resoverall_stock_price.fetchall())
            df1.columns = resoverall_stock_price.keys()

            # create df1
            df1 = df1.drop_duplicates(subset='Date')
            df1.index = df1['Date']
            df1_date_index = df1.drop(['Date'], axis=1)

            # create df2 and concat
            if strategy_sentiment == 'none_pass':
                # 不需要 concate
                df = df1_date_index

            else:
                # concate sentiment
                resoverall_sentiment = connection.execute(model_mysql_query.sql_strategy_sentiment(source, stock_code, start_date_datetime, end_date_datetime))

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
                df['MACD'], df['MACDsignal'], df['MACDhist'] = talib.MACD(df['Close'],
                                                                          fastperiod=12,
                                                                          slowperiod=26,
                                                                          signalperiod=9)

                df["B_MACD"] = df["MACD"].shift(1)
                df["B_MACDsignal"] = df["MACDsignal"].shift(1)

                # only MACD
                if strategy_sentiment == 'none_pass':
                    buy = []
                    sell = []
                    buy_count = 0
                    for i in range(len(df)):
                        if money >= df["Close"][i] and df["B_MACD"][i] < df["B_MACDsignal"][i] and df["MACD"][i] > df["MACDsignal"][i]:
                            buy.append(1)
                            sell.append(0)
                            buy_count += 1
                            money -= df["Close"][i]
                        elif buy_count > 0 and df["B_MACD"][i] > df["B_MACDsignal"][i] and df["MACD"][i] < df["MACDsignal"][i]:
                            sell.append(-1)
                            buy.append(0)
                            buy_count -= 1
                            money += df["Close"][i]
                        else:
                            buy.append(0)
                            sell.append(0)

                    df["buy"] = buy
                    df["sell"] = sell

                # MACD + sentiment over less
                elif strategy_sentiment == 'daily_sentiment_pass':
                    buy = []
                    sell = []
                    buy_count = 0
                    for i in range(len(df)):
                        if df['avg_valence'][i] < (float(sentiment_para_more) / 100 * 10 - 5) and df['avg_valence'][
                            i] > (
                                float(sentiment_para_less) / 100 * 10 - 5):
                            if money >= df["Close"][i] and df["B_MACD"][i] < df["B_MACDsignal"][i] and df["MACD"][i] > df["MACDsignal"][i]:
                                buy.append(1)
                                sell.append(0)
                                buy_count += 1
                                money -= df["Close"][i]
                            elif buy_count > 0 and df["B_MACD"][i] > df["B_MACDsignal"][i] and df["MACD"][i] < df["MACDsignal"][i]:
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

                # MACD + sentiment to negative
                elif strategy_sentiment == 'to_negative_pass':
                    buy = []
                    sell = []
                    buy_count = 0
                    for i in range(len(df)):
                        if i > 0:
                            if money >= df["Close"][i] and df["B_MACD"][i] < df["B_MACDsignal"][i] and df["MACD"][i] > df["MACDsignal"][i]:
                                buy.append(1)
                                sell.append(0)
                                buy_count += 1
                                money -= df["Close"][i]
                            elif buy_count > 0 and df["B_MACD"][i] > df["B_MACDsignal"][i] and df["MACD"][i] < df["MACDsignal"][i]:
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

                # MACD + sentiment to positive
                elif strategy_sentiment == 'to_positive_pass':
                    buy = []
                    sell = []
                    buy_count = 0
                    for i in range(len(df)):
                        if i > 0:
                            if money >= df["Close"][i] and df["B_MACD"][i] < df["B_MACDsignal"][i] and df["MACD"][i] > df["MACDsignal"][i]:
                                buy.append(1)
                                sell.append(0)
                                buy_count += 1
                                money -= df["Close"][i]
                            elif buy_count > 0 and df["B_MACD"][i] > df["B_MACDsignal"][i] and df["MACD"][i] < df["MACDsignal"][i]:
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

            # print(df)

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
            if strategy_sentiment != 'none_pass':
                df['avg_valence'] = (df['avg_valence'] + 5) * 10 / 100
            else:
                pass

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

                elif strategy_line == 'macd_line' and strategy_sentiment != 'none_pass':
                    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),
                                mpf.make_addplot(df["MACD"], panel=2, color="b"),
                                mpf.make_addplot(df["MACDsignal"], panel=2, color="r"),
                                mpf.make_addplot(df["MACDhist"], panel=2, color="g", type='bar'),
                                mpf.make_addplot(df["avg_valence"], panel=3, color="b")
                                ]

                elif strategy_line == 'macd_line' and strategy_sentiment == 'none_pass':
                    add_plot = [mpf.make_addplot(df["buy_mark"], scatter=True, markersize=100, marker='v', color='r'),
                                mpf.make_addplot(df["sell_mark"], scatter=True, markersize=100, marker='^', color='g'),
                                mpf.make_addplot(df["MACD"], panel=2, color="b"),
                                mpf.make_addplot(df["MACDsignal"], panel=2, color="r"),
                                mpf.make_addplot(df["MACDhist"], panel=2, color="g", type='bar'),
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
                flash('沒有交易點', 'danger')
                print('沒有交易點')
                return redirect(url_for('strategy.strategy_page'))
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
                    path = os.path.join(BASEDIR, "static/img/report", filename)
                    print(path)
                    mpf.plot(df, **kwargs, savefig=path)
                    print(filename)
                    print(path)

                except:
                    print('沒有交易點')
                    flash('沒有交易點', 'danger')
                    return redirect(url_for('strategy.strategy_page'))

                else:
                    s3_save_filename = filename + '.png'
                    s3_save_path = os.path.join(BASEDIR, "static/img/report", s3_save_filename)
                    print(s3_save_path)
                    # open file
                    pil_image = Image.open(s3_save_path)
                    # Save the image to an in-memory file
                    in_mem_file = io.BytesIO()
                    pil_image.save(in_mem_file, format=pil_image.format)
                    in_mem_file.seek(0)
                    upload_file(uid, in_mem_file, s3_save_filename, BUCKET_NAME, OBJECT_PATH)
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

                today_strftime, yesterday_strftime = get_today_yesterday()


                strategy_backtest_tuple = (uid, stock_code, start_date, end_date, strategy_line, strategy_in, strategy_in_para, strategy_out, strategy_out_para,
                                           strategy_sentiment, source, sentiment_para_more, sentiment_para_less,
                                           set_money, discount, total_buy_count, total_sell_count, total_return_rate, height_return, lowest_return,
                                           total_win, total_lose, total_trade, win_rate, avg_return_rate, irr, file_path, today_strftime)

                sql_insert_strategy_backtest = "INSERT INTO `strategy_backtest` (`user_id`, `stock_code`, `start_date`, `end_date`, \
                                                                                 `strategy_line`, `strategy_in`, `strategy_in_para`, `strategy_out`, `strategy_out_para`, \
                                                                                 `strategy_sentiment`, `source`, `sentiment_para_more`, `sentiment_para_less`, `seed_money`, \
                                                                                 `discount`, `total_buy_count`, `total_sell_count`, `total_return_rate`, `highest_return`, \
                                                                                 `lowest_return`, `total_win`, `total_lose`, `total_trade`, `win_rate`, `avg_return_rate`, \
                                                                                 `irr`, `file_path`, `create_date`) \
                                                                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
                db_mysql.insert_tb(sql_insert_strategy_backtest, strategy_backtest_tuple)

                return redirect(url_for('backtest.backtest_page'))

