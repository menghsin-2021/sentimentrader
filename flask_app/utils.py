import os
from flask import flash, request, render_template, Response
from model import model_mysql_query
from model import model_mysql
import config
from datetime import datetime, timedelta

# user
from hashlib import pbkdf2_hmac
import jwt

# s3
import boto3

# strategy
import mplfinance as mpf
import pandas as pd
from PIL import Image
import io


SECRET_KEY = config.SECRET_KEY
BUCKET_NAME = config.BUCKET_NAME
OBJECT_PATH = config.OBJECT_PATH

# S3 photo path
S3_PHOTO_PATH = config.S3_PHOTO_PATH

# basedir
BASEDIR = config.BASEDIR

DBNAME = config.DBNAME

# for all page check token
def get_cookie_check():
    token = request.cookies.get('token')
    expire_time = 3600

    if not token:
        flash('需要登入', 'danger')
        return render_template('login.html')
    else:
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], issuer='stock-sentimentrader.com', audience='www.stock-sentimentrader.com', verify_iss=expire_time)
            user_email = decoded_token['sub']
        except jwt.exceptions.InvalidSignatureError:
            return Response('Signature verification failed', status=403)
        except jwt.exceptions.ExpiredSignatureError:
            return Response('Signature has expired', status=403)
        except jwt.exceptions.InvalidIssuerError:
            return Response('Invalid issuer', status=403)
        except jwt.exceptions.InvalidAudienceError:
            return Response('Invalid audience', status=403)
        except:
            flash('需要登入', 'danger')
            return render_template('login.html')
        else:
            sql_uid = "SELECT `id` as `uid` \
                      FROM `user` \
                      WHERE `email` = '{}'".format(user_email)
            db_mysql = model_mysql.DbWrapperMysql(DBNAME)
            uid = db_mysql.query_tb_one(sql_uid)[0]

            return uid

class SocialVolumeFetch:
    def __init__(self):
        pass

    def fetch_social_volume(self, category=None, source=None, duration=None):
        # create sql
        if category == None:
            query_tuple = None
            sql_social_volume = model_mysql_query.sql_social_volume

        elif category == 'electric' or category == 'electric_car':
            category_both = 'electric_electric_car'
            query_tuple = (source, duration, category, category_both)
            sql_social_volume = model_mysql_query.sql_social_volume_duration_electric

        else:
            query_tuple = (source, duration, category)
            sql_social_volume = model_mysql_query.sql_social_volume_duration_another_category

        db_mysql = model_mysql.DbWrapperMysqlDict(DBNAME)
        result = db_mysql.query_tb_all(sql_social_volume, query_tuple)
        stock_name_code = [f"{word_count['stock_name']}, {word_count['stock_code']}" for word_count in result]
        stock_count = [int(word_count['count']) for word_count in result]
        article_count = [int(word_count['article_count']) for word_count in result]

        return stock_name_code, stock_count, article_count


class StockSentimentFetch:
    def __init__(self):
        pass

    def fetch_stock_price(self, stock_code):
        db_mysql = model_mysql.DbWrapperMysqlDict(DBNAME)
        sql_stock_price = model_mysql_query.sql_stock_price
        result = db_mysql.query_tb_all(sql_stock_price, (stock_code,))
        daily_stock_price = self.create_stock_price_json(result)

        return daily_stock_price

    def create_stock_price_json(self, result):
        date = [daily_info['days'] for daily_info in result]
        open = [daily_info['open'] if daily_info['open'] is not None else 0 for daily_info in result]
        low = [daily_info['low'] if daily_info['low'] is not None else 0 for daily_info in result]
        high = [daily_info['high'] if daily_info['high'] is not None else 0 for daily_info in result]
        close = [daily_info['close'] if daily_info['close'] is not None else 0 for daily_info in result]
        volume = [daily_info['volume'] if daily_info['volume'] is not None else 0 for daily_info in result]
        stock_price = {
            'date': date,
            'open': open,
            'low': low,
            'high': high,
            'close': close,
            'volume': volume
        }
        return stock_price

    def fetch_sentiment(self, source, stock_code):
        db_mysql = model_mysql.DbWrapperMysqlDict(DBNAME)
        sql_sentiment = model_mysql_query.sql_sentiment
        result = db_mysql.query_tb_all(sql_sentiment, (source, stock_code))
        daily_sentiment = self.create_sentiment_json(result)

        return daily_sentiment

    def create_sentiment_json(self, result):
        date = [daily_info['days'] for daily_info in result]
        chosen_stock_name = result[0]['stock_name']
        sum_valence = [daily_info['sum_valence'] for daily_info in result]
        avg_valence = [daily_info['avg_valence'] for daily_info in result]
        sum_arousal = [daily_info['sum_arousal'] for daily_info in result]
        avg_arousal = [daily_info['avg_arousal'] for daily_info in result]
        sum_sentiment = [int(daily_info['sum_sentiment']) for daily_info in result]

        shift_grade = 5
        total_grade = 10
        percent = 100
        total_angular = 180

        avg_valence_now = int((avg_valence[0] + shift_grade) / total_grade * percent)
        avg_arousal_now = int((avg_arousal[0] + shift_grade) / total_grade * percent)
        avg_valence_angular = int(avg_valence_now / percent * total_angular)

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
            'chosen_stock_name': chosen_stock_name
        }

        return sentiment

    def redis_tag(self, stock_code, source):
        tag_stock_price = str(stock_code) + '_' + 'stock_price'
        tag_sentiment = str(stock_code) + '_' + 'sentiment' + '_' + source

        return tag_stock_price, tag_sentiment


# strategy api
class GetDayStr:
    def __init__(self):
        pass

    def today_yesterday(self):
        today_strftime = datetime.today().strftime('%Y-%m-%d')
        yesterday_strftime = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

        return today_strftime, yesterday_strftime


    def get_day_before(self, days):
        days_ago_strftime = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d') + ' 00:00:00'

        return days_ago_strftime

class MarketInTime:
    def __init__(self):
        pass

    def buy_by_macd(self, money, df, i, buy_count):
        if money >= df["Close"][i] and df["B_MACD"][i] < df["B_MACDsignal"][i] and df["MACD"][i] > df["MACDsignal"][i]:
            buy_point = 1
            buy_count += 1
            buy_price = df["Close"][i]

        elif buy_count > 0 and df["B_MACD"][i] > df["B_MACDsignal"][i] and df["MACD"][i] < df["MACDsignal"][i]:
            buy_point = -1
            buy_count -= 1
            buy_price = -df["Close"][i]

        else:
            buy_point = 0
            buy_price = 0

        return buy_point, buy_count, buy_price

    def buy_by_kd(self, money, df, i, buy_count):
        if money >= df["Close"][i] and df["B_K"][i] < df["B_D"][i] and df["K"][i] > df["D"][i]:
            buy_point = 1
            buy_count += 1
            buy_price = df["Close"][i]
        elif buy_count > 0 and df["B_K"][i] > df["B_D"][i] and df["K"][i] < df["D"][i]:
            buy_point = -1
            buy_count -= 1
            buy_price = -df["Close"][i]
        else:
            buy_point = 0
            buy_price = 0

        return buy_point, buy_count, buy_price

    def buy_by_increase_in(self, money, df, i, buy_count, strategy_in_para, strategy_out_para):
        if i > 1:
            if money >= df["Close"][i] and df["Close"][i] / (1 + strategy_in_para / 100) > \
                    df["Close"][i - 1] and df["Close"][i - 1] / (1 + strategy_in_para / 100) > \
                    df["Close"][i - 2]:
                buy_point = 1
                buy_count += 1
                buy_price = df["Close"][i]
            elif buy_count > 0 and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                i - 1] and df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                buy_point = -1
                buy_count -= 1
                buy_price = -df["Close"][i]
            else:
                buy_point = 0
                buy_price = 0

        else:
            buy_point = 0
            buy_price = 0

        return buy_point, buy_count, buy_price

    def buy_by_increase_out(self, money, df, i, buy_count, strategy_in_para, strategy_out_para):
        if i > 1:
            if money >= df["Close"][i] and df["Close"][i] / (1 - strategy_out_para / 100) < df["Close"][
                i - 1] and \
                    df["Close"][i - 1] / (1 - strategy_out_para / 100) < df["Close"][i - 2]:
                buy_point = 1
                buy_count += 1
                buy_price = df["Close"][i]
            elif buy_count > 0 and df["Close"][i] / (1 + strategy_in_para / 100) > df["Close"][i - 1] and \
                    df["Close"][i - 1] / (1 + strategy_in_para / 100) > df["Close"][i - 2]:
                buy_point = -1
                buy_count -= 1
                buy_price = -df["Close"][i]
            else:
                buy_point = 0
                buy_price = 0
        else:
            buy_point = 0
            buy_price = 0

        return buy_point, buy_count, buy_price

class DrawMpf:
    def __init__(self):
        pass

    def add_plot_parameter(self, length_of_buy_mark, length_of_sell_mark, strategy_line, strategy_sentiment, df):
        if length_of_buy_mark > 0 and length_of_sell_mark > 0:
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

        return add_plot

    def get_mpf_plot(self, df, stock_code, add_plot):
        df.index = pd.DatetimeIndex(df.index)
        stock_id = "{}.TW".format(stock_code)
        mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, rc={'font.size': 14})
        kwargs = dict(type='candle', volume=True, figsize=(20, 10), title=stock_id, style=s, addplot=add_plot)
        timestamp = int(datetime.today().timestamp())
        timestamp_str = str(timestamp)
        filename = f"{stock_code}_{timestamp_str}"
        path = os.path.join(BASEDIR, "static/img/report", filename)
        mpf.plot(df, **kwargs, savefig=path)

        return filename

    # S3 upload
    def upload_file(self, uid, file, file_name, bucket_name, object_path=None):
        s3_client = boto3.client('s3')
        object = object_path + '/' + str(uid) + '/' + file_name

        try:
            s3_client.put_object(Body=file, Bucket=bucket_name, Key=object, ContentType='image/png')
            print('upload success')
        except:
            print('fail')
            return False

        else:
            return file_name

    def upload_figure_s3(self, filename, uid):
        s3_save_filename = filename + '.png'
        s3_save_path = os.path.join(BASEDIR, "static/img/report", s3_save_filename)
        # open file
        pil_image = Image.open(s3_save_path)
        # Save the image to an in-memory file
        in_mem_file = io.BytesIO()
        pil_image.save(in_mem_file, format=pil_image.format)
        in_mem_file.seek(0)
        self.upload_file(uid, in_mem_file, s3_save_filename, BUCKET_NAME, OBJECT_PATH)
        file_path = f"{S3_PHOTO_PATH}/{uid}/{s3_save_filename}"

        return file_path



# backtest api
# S3 delete
def delete_file(bucket_name, object_path, uid, file_name):
    try:
        client = boto3.client('s3')
        object = object_path + '/' + str(uid) + '/' + file_name
        client.delete_object(Bucket=bucket_name, Key=object)
        print('delete success')
        return True

    except:
        print('delete fail')
        return False



# user api
class Checkjwt:
    def __init__(self):
        pass

    def generate_salt(self):
        salt = os.urandom(16)
        return salt.hex()  # 轉換16進制


    def generate_hash(self, plain_password, password_salt):
        # 基於密碼的金鑰派生函式2以HMAC為偽隨機函式。
        password_hash = pbkdf2_hmac(
            "sha256",  # hash name  返回一個sha256物件；把字串轉換為位元組形式；
            b"%b" % bytes(plain_password, "utf-8"),  # password 二進制數據  原本: b"%b" % bytes(plain_password, "utf-8")
            b"%b" % bytes(password_salt, "utf-8"),  # salt 二進制數據  原本: b"%b" % bytes(password_salt, "utf-8")
            10000,  # iterations
        )
        return password_hash.hex()  # 轉換16進制


    def b_type_to_str(self, b_type):
        if type(b_type) is bytes:
            b_type = str(b_type)[2:-1]
        else:
            b_type = str(b_type)
        return b_type


    def check_basic_auth_signup(self, name, email, pwd, con_pwd):
        if name and email and pwd:
            return len(name) <= 255 and len(email) <= 255 and len(pwd) <= 255 and pwd == con_pwd

        else:
            return False


    def check_basic_auth_signin(self, email, pwd):
        if email and pwd:
            return len(email) <= 255 and len(pwd) <= 255

        else:
            return False


    def set_token(self, iss, sub, aud, iat, nbf, exp, jti):
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




# change code to name
class GetName:
    def __init__(self):
        pass

    def category(self, code):
        category_name = {
            "electric_electric_car": "電動車",
            "electric_car": "電動車",
            "electric": "電子資訊",
            "sail": "航運",
            "biotech": "生技",
            "finance": "金融",
            "stock_market": "台積電",
        }

        try:
            return category_name[code]

        except:
            return None

    def source(self, code):
        source_name = {
            "ptt": "PTT 論壇",
            "cnyes": "鉅亨網",
        }

        try:
            return source_name[code]

        except:
            return None

    def duration(self, code):
        duration_name = {
            "daily": "當日",
            "weekly": "當周",
            "monthly": "當月",
            "yearly": "一年內",
            "three_yearly": "三年內"
        }
        try:
            return duration_name[code]

        except:
            return None

    def strategy_line(self, code):
        strategy_line_name = {
            "none": "--",
            "undefined": "--",
            "kdj_line": "ＫＤ線交叉",
            "macd_line": "ＭＡＣＤ線交叉",
            "none_line": "自訂",
        }
        try:
            return strategy_line_name[code]

        except:
            return None

    def strategy_in(self, code):
        strategy_in_name = {
            "none": "--",
            "increase_in": "股價連續上漲(3日)",
            "decrease_in": "股價連續下跌(3日)"
        }
        try:
            return strategy_in_name[code]

        except:
            return None

    def strategy_out(self, code):
        strategy_out_name = {
            "none": "--",
            "increase_out": "股價連續上漲(3日)",
            "decrease_out": "股價連續下跌(3日)"
        }
        try:
            return strategy_out_name[code]

        except:
            return None

    def strategy_sentiment(self, code):
        strategy_sentiment_name = {
            "none_pass": "--",
            "daily_sentiment_pass": "當日情緒分數",
            "to_negative_pass": "正轉負",
            "to_positive_pass": "負轉正",
        }
        try:
            return strategy_sentiment_name[code]

        except:
            return None