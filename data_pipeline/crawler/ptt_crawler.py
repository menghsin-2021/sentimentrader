import requests
from bs4 import BeautifulSoup
import re
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


def fetch_content_url(page):
    list_url = "https://www.ptt.cc/bbs/Stock/index{}.html".format(page)
    print("URL:", list_url)
    print("parse page: ", page)
    r = requests.get(list_url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    links = soup.find_all("a", href=re.compile("/bbs/Stock/M."))
    content_urls = ["https://www.ptt.cc{}".format(link.get('href')) for link in links]
    return content_urls

def fetch_content_page(content_urls):
    ptt_post_list = []
    for url in content_urls:
        print("now parse URL:", url)
        r = requests.get(url, headers=HEADERS)
        web_content = r.text
        soup = BeautifulSoup(web_content, 'html.parser')
        spans = soup.find_all("span", class_="article-meta-value")

        author = spans[0].getText()
        title = spans[2].getText()
        create_time = spans[3].getText()

        main_container = soup.find(id='main-container')
        all_text = main_container.text
        pre_text = all_text.split('--')[0]
        texts = pre_text.split('\n')
        contents = texts[2:]
        content = '\n'.join(contents)

        if len(content) > 0:
            pre_all_response_list = [response.string for response in soup.find_all("span", class_="push-content")]
            all_response_list = [response.strip(":") for response in pre_all_response_list if response]

            ptt_post = {'author': author,
                        'title': title,
                        'create_time': create_time,
                        'content': content,
                        'all_response_list': all_response_list}

            ptt_post_list.append(ptt_post)
            time.sleep(0.5)

    return ptt_post_list

if __name__ == '__main__':
    for i in range(5005, 5004, -1):
        try:
            content_urls = fetch_content_url(i)
            # fetch page
            ptt_post_list = fetch_content_page(content_urls)
            db_mongo = model_mongo.DbWrapperMongo()
            # col_name = "ptt"
            col_name = "test"
            db_mongo.insert_many(col_name, ptt_post_list)
            time.sleep(0.5)
        except:
            continue

