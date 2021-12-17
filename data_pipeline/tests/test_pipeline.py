import model_mongo
import model_mysql
from datetime import datetime, timedelta
import requests
from pprint import pprint

month_dict = {1: ["Jan", '01'], 2: ["Feb", '02'], 3: ["Mar", '03'], 4: ["Apr", '04'],
                  5: ["May", '05'], 6: ["Jun", '06'], 7: ["Jul", '07'], 8: ["Aug", '08'],
                  9: ["Sep", '09'], 10: ["Oct", '10'], 11: ["Nov", '11'], 12: ["Dec", '12']}

SOURCES = ['ptt', 'cnyes']

def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d')
    year = int(today_strftime.split('-')[0])
    month = int(today_strftime.split('-')[1])
    day = int(today_strftime.split('-')[2])
    return year, month, day

def get_yesterday():
    yesterday_strftime = (datetime.today()-timedelta(days=1)).strftime('%Y-%m-%d')
    year = int(yesterday_strftime.split('-')[0])
    month = int(yesterday_strftime.split('-')[1])
    day = int(yesterday_strftime.split('-')[2])
    return year, month, day

def fetch_daily_data(year, month, day, source):
    if source == 'ptt':
        month = month_dict[month][0]
        db_mongo = model_mongo.DbWrapperMongo()
        if day < 10:
            query_dict = {'create_time': {'$regex': f"{month}  {day}(.*){year}"}}
            col_name = 'ptt'
            rows = db_mongo.find(col_name, query_dict)
            rows = [row for row in rows]
            return rows
        elif day >= 10:
            query_dict = {'create_time': {'$regex': f"{month} {day}(.*){year}"}}
            col_name = 'ptt'
            rows = db_mongo.find(col_name, query_dict)
            rows = [row for row in rows]
            return rows

    elif source == 'cnyes':
        db_mongo = model_mongo.DbWrapperMongo()
        if month < 10:
            month = f"0{month}"
        if day < 10:
            day = f"0{day}"
        query_dict = {'date': {'$regex': f"{year}/{month}/{day}"}}
        col_name = 'cnyes'
        rows = db_mongo.find(col_name, query_dict)
        rows = [row for row in rows]
        return rows

    else:
        return None



def iso_date(year, month, day):
    if month < 10:
        month = "0" + str(month)
    if day < 10:
        day = "0" + str(day)
    try:
        create_time = datetime.fromisoformat(f'{year}-{month}-{day}')
    except:
        return None
    else:
        return create_time


def fetch_article_tag(year, month, day, col_name):
    db_mongo = model_mongo.DbWrapperMongo()
    create_time = iso_date(year, month, day)
    query_dict = {"create_time": create_time}
    rows = db_mongo.find(col_name, query_dict)
    rows = [row for row in rows]
    return create_time, rows


def fetch_stock_number(table, date, source=None, date_tomorrow=None):
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    if table == 'daily_social_volume':
        sql_stock_number = "SELECT COUNT(*) as `total` \
                             FROM `daily_social_volume` \
                             WHERE `source` = '{}' \
                             AND `date` = '{}'".format(source, date)

    elif table == 'daily_sentiment':
        sql_stock_number = "SELECT COUNT(*) as `total` \
                             FROM `daily_sentiment` \
                             WHERE `source` = '{}' \
                             AND `date` = '{}'".format(source, date)

    elif table == 'daily_stock_price':
        sql_stock_number = "SELECT COUNT(DISTINCT(`stock_code`)) as `total` \
                             FROM `daily_stock_price` \
                             WHERE `date` > '{}' AND `date` < '{}'".format(date, date_tomorrow)
    else:
        return None

    result = db_mysql.query_tb_one(sql_stock_number)
    stock_number = result[0]

    return stock_number


def crawl_stock_price_twse(year, month, day):
    if month < 10:
        month = "0" + str(month)

    if day < 10:
        day = f"0{day}"

    date = f'{year}{month}01'
    stock_code = '2330'

    r = requests.get(f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?date={date}&stockNo={stock_code}')
    stock_price_json = r.json()
    stock_price_datas = stock_price_json['data']

    stock_price = {
                'open': None,
                'high': None,
                'low': None,
                'close': None
            }

    year = year - 1911
    for stock_price_data in stock_price_datas:
        date = f'{year}/{month}/{day}'
        if date in stock_price_data:
        # if f'110/12/01' in stock_price_data:
            stock_price['open'] = round(float(stock_price_data[3]), 1)
            stock_price['high'] = round(float(stock_price_data[4]), 1)
            stock_price['low'] = round(float(stock_price_data[5]), 1)
            stock_price['close'] = round(float(stock_price_data[6]), 1)
            # print(stock_price)
        else:
            continue

    return stock_price


def fetch_stock_price(date, date_tomorrow):
    print(date, date_tomorrow)
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    stock_code = '2330'
    sql_stock_price = "SELECT `open`, `high`, `low`, `close`\
                                 FROM `daily_stock_price` \
                                 WHERE `date` > '{}' AND `date` < '{}' AND stock_code = '{}'".format(date, date_tomorrow, stock_code)
    # print(sql_stock_price)
    result = db_mysql.query_tb_one(sql_stock_price)
    if not result:
        stock_price = {
            'open': None,
            'high': None,
            'low': None,
            'close': None
        }

    else:
        stock_price = {
            'open': result[0],
            'high': result[1],
            'low': result[2],
            'close': result[3]
        }

    return stock_price


if __name__ == '__main__':
    year, month, day = get_yesterday()
    for i in range(year, year + 1):
        for j in range(month, month + 1):
            for k in range(day, day + 1):
                year_fetch = i
                month_fetch = j
                day_fetch = k
                date = iso_date(year_fetch, month_fetch, day_fetch)
                date_tomorrow = date + timedelta(days=1)
                # date_yesterday = date - timedelta(days=1)
                print(f'calculate {year_fetch}-{month_fetch}-{day_fetch}')

                count_dict = {}
                count_dict["create_time"] = date
                for SOURCE in SOURCES:
                    count_dict[SOURCE] = {}
                    count_dict['stock_price'] = {}
                    # fetch crawled data
                    try:
                        rows = fetch_daily_data(year_fetch, month_fetch, day_fetch, SOURCE)

                    except:
                        print("no date")
                        count_dict[SOURCE]['crawl'] = 0
                        continue
                    else:
                        # aggregate text
                        crawl_numbers = len(rows)
                        count_dict[SOURCE]['crawl'] = crawl_numbers
                        print(SOURCE, ' article_today_numbers:', crawl_numbers)

                    # fetch cut data
                    try:
                        date, rows = fetch_article_tag(year_fetch, month_fetch, day_fetch, f'{SOURCE}_stock_tag')
                    except:
                        print("no date")
                        count_dict[SOURCE]['cut'] = 0
                        continue
                    else:
                        # total words in day
                        if not date:
                            count_dict[SOURCE]['cut'] = 0
                            continue
                        else:
                            # print(date)
                            cut_numbers = len(rows)
                            count_dict[SOURCE]['cut'] = cut_numbers
                            print(SOURCE, ' article numbers after cut: ', len(rows))
                            if count_dict[SOURCE]['crawl'] <= 0 and count_dict[SOURCE]['crawl'] != count_dict[SOURCE]['cut']:
                                count_dict[SOURCE]['check'] = 'fail'
                            else:
                                count_dict[SOURCE]['check'] = 'pass'

                    # fetch stock number from social_volume and sentiment
                    try:
                        stock_number_social_volume = fetch_stock_number('daily_social_volume', date, SOURCE)
                        stock_number_sentiment = fetch_stock_number('daily_sentiment', date, SOURCE)

                    except:
                        print("no date")
                        continue

                    else:
                        print(SOURCE, ' stock numbers after cut from social volume: ', stock_number_social_volume)
                        print(SOURCE, ' stock numbers after cut from sentiment: ', stock_number_sentiment)
                        count_dict[SOURCE]['social_volume'] = stock_number_social_volume
                        count_dict[SOURCE]['sentiment'] = stock_number_sentiment

                    if count_dict[SOURCE]['crawl'] != 480 and count_dict[SOURCE]['social_volume'] != count_dict[SOURCE]['sentiment']:
                        count_dict[SOURCE]['check'] = 'fail'

                # fetch stock number from stock_price
                try:
                    stock_number_stock_price = fetch_stock_number('daily_stock_price', date, None, date_tomorrow)
                except:
                    count_dict['stock_price_number'] = 0
                    print("no date")
                else:
                    print('stock numbers from daily_stock_price: ', stock_number_stock_price)
                    count_dict['stock_price']['crawl'] = stock_number_stock_price

                # request stock price from twse
                try:
                    stock_price_twse = crawl_stock_price_twse(year_fetch, month_fetch, day_fetch)
                    stock_price_yahoo = fetch_stock_price(date, date_tomorrow)
                except:
                    print("no data")

                else:
                    print(stock_price_twse)
                    print(stock_price_yahoo)
                    count_dict['stock_price']['2330_twse'] = stock_price_twse
                    count_dict['stock_price']['2330_yahoo'] = stock_price_yahoo
                    if stock_price_twse['open'] == stock_price_yahoo['open']:
                        print('stock_price_open: pass')
                        if stock_price_twse['high'] == stock_price_yahoo['high']:
                            print('stock_price_high: pass')
                            if stock_price_twse['low'] == stock_price_yahoo['low']:
                                print('stock_price_low: pass')
                                if stock_price_twse['close'] == stock_price_yahoo['close']:
                                    print('stock_price_close: pass')
                                    count_dict['stock_price']['check'] = 'pass'
                                else:
                                    print('stock_price_close: fail')
                                    count_dict['stock_price']['check'] = 'fail'
                            else:
                                print('stock_price_low: fail')
                                count_dict['stock_price']['check'] = 'fail'
                        else:
                            print('stock_price_high: fail')
                            count_dict['stock_price']['check'] = 'fail'
                    else:
                        print('stock_price_open: fail')
                        count_dict['stock_price']['check'] = 'fail'

                pprint(count_dict)
                db_mongo = model_mongo.DbWrapperMongo()
                col_name = "stabilization"
                # col_name = "test"
                db_mongo.insert_one(col_name, count_dict)