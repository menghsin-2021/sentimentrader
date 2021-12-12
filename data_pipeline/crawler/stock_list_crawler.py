import time
import requests
from bs4 import BeautifulSoup
import re


def fetch_stock_list(kind):
    url = f"https://tw.stock.yahoo.com/h/kimosel.php?tse=1&cat={kind}&form=menu&form_id=stock_id&form_name=stock_name&domain=0"

    headers = {
        'Cookie': 'A1=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko; A1S=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko&j=WORLD; A3=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko; B=5k8ksa5gmsahv&b=3&s=qd; GUC=AQEBAQFhb35heEIfngTT; cmp=t=1634610354&j=0; A1S=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko&j=US',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'tw.stock.yahoo.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Accept-Language': 'zh-tw',
        'Referer': 'https://tw.stock.yahoo.com/h/kimosel.php?tse=1&cat=%E9%9B%BB%E8%85%A6%E9%80%B1%E9%82%8A&form=menu&form_id=stock_id&form_name=stock_name&domain=0',
        'Connection': 'keep-alive'
    }

    resp = requests.request("GET", url, headers=headers)
    web_content = resp.text
    soup = BeautifulSoup(web_content, 'html.parser')
    a_tags = soup.find_all("a", href=re.compile(r'javascript:setid'))
    stock_code_names = [stock_code_name.get('href').split("'") for stock_code_name in a_tags]
    stock_code_name_dict_list = [{'stock_code': stock_code_name[1], 'stock_name': stock_code_name[3]} for stock_code_name in stock_code_names]
    stock_code_list = [stock_code_name_dict['stock_code'] for stock_code_name_dict in stock_code_name_dict_list]
    stock_name_list = [stock_code_name_dict['stock_name'] for stock_code_name_dict in stock_code_name_dict_list]

    return stock_code_name_dict_list, stock_code_list, stock_name_list


# fetch_stock_list
stock_kind_list = ['電腦週邊', '光電', '通訊網路', '電子零組件', '電子通路', '資訊服務', '其他電子', '航運', '生技', '金融業']
all_stock_name_list = []
all_stock_code_list = []
for stock_kind in stock_kind_list:
    stock_code_name_dict_list, stock_code_list, stock_name_list = fetch_stock_list(stock_kind)
    for stock_name in stock_name_list:
        all_stock_name_list.append(stock_name)
    for stock_code in stock_code_list:
        all_stock_code_list.append(stock_code)
    time.sleep(1)

for stock_name in all_stock_name_list:
    print(f"{stock_name} 1 N")

for stock_code in all_stock_code_list:
    print(f"{stock_code} 1 N")




