from datetime import datetime, timedelta
import json
import time
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import sqlalchemy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config
from stock_list import all_list



# from selenium import webdriver
options = Options()
options.add_argument("--headless")
options.add_argument("window-size=1400,1500")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")

# db var
DBHOST = config.DBHOST
DBUSER = config.DBUSER
DBPASSWORD = config.DBPASSWORD
DBNAME = config.DBNAME
RDSPORT = 3306

CHROMEDRIVERPATH = config.CHROMEDRIVERPATH


def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d') + 'T00:00:00.000+00:00'
    timestamp_today = int(datetime.fromisoformat(today_strftime).timestamp())
    timestamp_day_before = int(
        (datetime.fromisoformat(today_strftime) - timedelta(days=1)).timestamp())  # for automation
    print(timestamp_today)
    print(timestamp_day_before)
    return timestamp_day_before, timestamp_today


def craw_stock(stock_code, timestamp_start, timestamp_end):
    TWO = [1599, 2237, 4503, 4721, 4738, 5227, 5233, 5439, 6121, 6275, 8038, 8109, 8171, 8183, 8358, 8933, 8937]

    if stock_code not in TWO:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW?period1={timestamp_start}&period2={timestamp_end}&interval=1d&events=history&=hP2rOschxO0"
    else:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TWO?period1={timestamp_start}&period2={timestamp_end}&interval=1d&events=history&=hP2rOschxO0"

    # on local
    driver = webdriver.Chrome(CHROMEDRIVERPATH)

    # on EC2
    # driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)

    driver.get(url)
    # wait for loading
    driver.implicitly_wait(15)  # seconds
    html = driver.page_source
    soup = BeautifulSoup(html)
    data = json.loads(soup.text)
    df = pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0],
                      index=pd.to_datetime(np.array(data['chart']['result'][0]['timestamp']) * 1000 * 1000 * 1000))

    df['stock_code'] = stock_code
    driver.quit()
    return df


# save datafram into mysql
def df_row_insert(df):
    engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                           .format(user=DBUSER,
                                   pw=DBPASSWORD,
                                   db=DBNAME,
                                   host=DBHOST))
    df.to_sql(f"daily_stock_price", con=engine, if_exists='append', chunksize=1000, index=True, index_label="date",
              dtype={'date': sqlalchemy.types.DateTime,
                     'low': sqlalchemy.types.Float(precision=2, asdecimal=True),
                     'open': sqlalchemy.types.Float(precision=2, asdecimal=True),
                     'high': sqlalchemy.types.Float(precision=2, asdecimal=True),
                     'close': sqlalchemy.types.Float(precision=2, asdecimal=True),
                     'volume': sqlalchemy.types.BigInteger,
                     'stock_code': sqlalchemy.types.VARCHAR(length=255)
                     })


if __name__ == "__main__":
    timestamp_day_before, timestamp_today = get_today()
    stock_fail_1st = []
    stock_fail_2nd = []
    for list in all_list:
        for stock_code in list:
            try:
                df = craw_stock(stock_code, timestamp_day_before, timestamp_today)
                df_row_insert(df)
                time.sleep(1)
            except:
                print(f"{stock_code} fail")
                stock_fail_1st.append(stock_code)
                continue

    for stock_code in stock_fail_1st:
        try:
            df = craw_stock(stock_code, timestamp_day_before, timestamp_today)
            df_row_insert(df)
            time.sleep(1)
        except:
            print(f"{stock_code} fail")
            stock_fail_2nd.append(stock_code)
            continue

    for stock_code in stock_fail_2nd:
        try:
            df = craw_stock(stock_code, timestamp_day_before, timestamp_today)
            df_row_insert(df)
            time.sleep(1)
        except:
            print(f"{stock_code} fail")
            continue
