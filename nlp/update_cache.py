import requests
import config
import time
import stock_list

all_list = stock_list.all_list
secret_key = config.SECRET_KEY

url = 'https://www.stock-sentimentrader.com/set_sentiment_cache'

data_ptt = {'stock_code': '2610', 'source': 'cnyes', 'secret_key': secret_key}
requests.post(url, data=data_ptt)

for list in all_list:
    for stock_code in list:
        try:
            data_ptt = {'stock_code': stock_code, 'source': 'ptt', 'secret_key': secret_key}
            requests.post(url, data=data_ptt)
            time.sleep(1)
            data_cnyes = {'stock_code': stock_code, 'source': 'cnyes', 'secret_key': secret_key}
            requests.post(url, data=data_cnyes)
            time.sleep(1)
            print(f'set {stock_code} cache ok')
        except:
            print(f"{stock_code} fail")
            continue