from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
import re
from pprint import pprint
import model_mongo
import time

HEADERS = {
    'authority': 'scrapeme.live',
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
}


def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d') + 'T00:00:00.000+00:00'

    timestamp_test = int(datetime.fromisoformat('2021-11-03T00:00:00.000+00:00').timestamp())
    timestamp_today_zero = int(datetime.fromisoformat(today_strftime).timestamp())
    timestamp_today_now = int(datetime.today().timestamp())
    timestamp_tomorrow_zero = int((datetime.fromisoformat(today_strftime) + timedelta(days=1)).timestamp())  # for 自動化
    # timestamp_day_before_check = int(datetime.fromisoformat('2021-11-01T00:00:00.000+00:00').timestamp())
    # print(timestamp_test)  # 1635897600  2021-11-03T00:00:00.000+00:00
    # print(timestamp_today_zero)  # 1635984000  2021-11-04T00:00:00.000+00:00  起點
    # print(timestamp_today_now)  # 1636005498  2021-11-04 Now
    # print(timestamp_tomorrow_zero)  # 1636070400  2021-11-05T00:00:00.000+00:00  終點
    # print(timestamp_day_before_check)
    # timestamp_end = 1635811200  # 2021/11/02 00:00:00
    # timestamp_start = 1634947200  # 2021/10/23 00:00:00

    return timestamp_today_zero, timestamp_tomorrow_zero


def fetch_second_page():
    index_url = "https://www.ptt.cc/bbs/Stock/index.html"
    print("URL:", index_url)
    r = requests.get(index_url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    # pprint(soup)
    links = soup.find_all("a", href=re.compile("/bbs/Stock/index."), class_="wide")

    # pprint(links)
    page = [link.get('href') for link in links]
    regex = re.compile(r"(/bbs/Stock/index)(\d*)(.html)")
    match = regex.search(page[1])
    second_page = int(match.group(2))
    # print(second_page)

    return second_page


def fetch_content_url(page):
    list_url = "https://www.ptt.cc/bbs/Stock/index{}.html".format(page)
    print("URL:", list_url)
    print("parse page: ", page)
    # try:
    r = requests.get(list_url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    # pprint(soup)
    links = soup.find_all("a", href=re.compile("/bbs/Stock/M."))
    # pprint(links)
    content_urls = ["https://www.ptt.cc{}".format(link.get('href')) for link in links]
    return content_urls

def fetch_content_page(content_urls, timestamp_today_zero, timestamp_tomorrow_zero):
    ptt_post_list = []
    for url in content_urls:
        print("now parse URL:", url)

        regex = re.compile(r"(https://www.ptt.cc/bbs/Stock/M.)(\d*)")
        match = regex.search(url)
        timestamp_article = int(match.group(2))
        # print(timestamp_article)
        if timestamp_article < timestamp_today_zero or timestamp_article > timestamp_tomorrow_zero:
            continue
        else:
            try:
                r = requests.get(url, headers=HEADERS)
                web_content = r.text
                soup = BeautifulSoup(web_content, 'html.parser')
                spans = soup.find_all("span", class_="article-meta-value")
                # print(spans)
                author = spans[0].getText()
                title = spans[2].getText()
                create_time = spans[3].getText()
                # print(author, title, create_time)

                ##### 查找所有html 元素 抓出內容 #####
                main_container = soup.find(id='main-container')
                # 把所有文字都抓出來
                all_text = main_container.text
                # 把整個內容切割透過 "-- " 切割成2個陣列
                pre_text = all_text.split('--')[0]
                # 把每段文字 根據 '\n' 切開
                texts = pre_text.split('\n')
                # 如果你爬多篇你會發現
                contents = texts[2:]
                # 內容
                content = '\n'.join(contents)
                # print(content)

                if len(content) > 0:
                    pre_all_response_list = [response.string for response in soup.find_all("span", class_="push-content")]
                    all_response_list = [response.strip(":") for response in pre_all_response_list if response]
                    # print(all_response_list)

                    ptt_post = {'author': author,
                                'title': title,
                                'create_time': create_time,
                                'content': content,
                                'all_response_list': all_response_list}

                    ptt_post_list.append(ptt_post)
                    time.sleep(0.5)
                else:
                    continue
            except:
                continue

    return ptt_post_list

if __name__ == '__main__':
    timestamp_today_zero, timestamp_tomorrow_zero = get_today()
    second_page = fetch_second_page()
    start_page = second_page + 1
    end_page = second_page - 3
    # print(timestamp_today_zero)
    # print(timestamp_tomorrow_zero)
    # print(second_page)
    # print(start_page)
    # print(end_page)
    for i in range(start_page, end_page, -1):  # 11/2 back
        try:
            print(i)
            content_urls = fetch_content_url(i)
            # print(content_urls)

            # fetch page
            ptt_post_list = fetch_content_page(content_urls, timestamp_today_zero, timestamp_tomorrow_zero)
            # print(ptt_post_list)
            db_mongo = model_mongo.DbWrapperMongo()
            col_name = "ptt"
            # col_name = "test"
            db_mongo.insert_many(col_name, ptt_post_list)
            time.sleep(0.5)
        except:
            continue



# fetch one
    # author, title, create_time, content, all_response_list = fetch_content_one(content_urls)
    # db_mongo = model_mongo.DbWrapperMongo()
    # if len(content) > 0:
    #     db_mongo.insert_one("ptt", cnyes_post)


