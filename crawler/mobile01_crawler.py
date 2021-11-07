import requests
from bs4 import BeautifulSoup
import re
from pprint import pprint
from selenium import webdriver
import time
import model_mongo

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Cookie': '_ga=GA1.2.1349000075.1634377781; _gat_UA-121129530-1=1; _gat_UA-121129530-3=1; _gat_UA-124523494-1=1; _gat_UA-124523494-2=1; _gat_UA-808494-1=1; _gid=GA1.2.1455325638.1634377781; cto_bundle=fTW4XV9rVFFsbWklMkIlMkY5TFZCMzd5WWdtWGFVZWR2UkJJeUlnQiUyQkxSakZkd0dOemdtRmdRTGZUTUF2U2hKbm5hZEh2TlFDcXglMkIlMkYxS3pKU3cxS2d5UDdyR1RkVVpJNyUyRmp3UnJ1OUdDMlc5WWpUeXdCY1hjQXJPSnBuNzR5RXJBQW1RelZueA; __retfs=fSes-b78682a-d0bb-5588-44e0; _pbjs_userid_consent_data=3524755945110770; dable_uid=27036520.1634173382998; MID-uuid=7b063a10-2c8a-11ec-8f97-185d387c6d42; MID-uuid-p=19d41baa066b2e3d1e1d010827207154; PHPSESSID=03046dc739972fa8650c300c2e362a93; HobbyCat=1; HobbyCatuuid=525d36753b4dfadc53bc43fda8414f49; __cfruid=7adc2ee853031b8fae3f430718ef9c435b5e834a-1634378108; __fpid=a59d19b69fb583853024fa9c0542da50; __retuid=49f7ef9e-bef5-214c-2af2-aeab6e7ddc99; __cf_bm=kQzfn7f9o2zYo0xPBKYFNTXUqc4ZZzlC50J_gBKr4Hc-1634377780-0-Ab3TIgkD0T71ZzzBP2jkxQoLtjpAwKzcC5Sj92JVkeItNz7cByiszi4YzYPIKJS8oFQj2DSQJz3NmvPkJeFSJ8JoQBk2Ci2mifvMeJH7ih5LuQM0HX4y3bT1JvMyPTaVc+HKUxbDZK7BBvPRQdloum6tYcp/CvOPLFXej8e2dHzcKK/7mTi7xBoEtnOYDmIP6w==; _gcl_au=1.1.44667464.1634377781; _pubcid=204956a7-e7ff-4a3d-83dd-cc0c4e481928',
    'Host': 'www.mobile01.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-tw',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

def fetch_content_url(page):
    list_url = f"https://www.mobile01.com/topiclist.php?f=793&p={page}"
    print("URL:", list_url)
    # try:
    r = requests.get(list_url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    pprint(soup)
    # links = soup.find_all("a", href=re.compile("topicdetail.php"))
    # pprint(links)
    # content_urls = [f"https://www.ptt.cc{link.get('href')}" for link in links]
    # return content_urls


# fetch_content_url(1)


def fetch_content_url_selenium(page):
    driver = webdriver.Chrome('/usr/local/bin/chromedriver')
    driver.get(f"https://www.mobile01.com/topiclist.php?f=793&p={page}")
    # 等待網頁載入
    driver.implicitly_wait(15)  # seconds
    html = driver.page_source
    soup = BeautifulSoup(html)
    # pprint(soup)
    links = soup.find_all("a", href=re.compile(r"topicdetail.php?"))
    # pprint(links)
    content_urls = [f"https://www.mobile01.com/{link.get('href')}" for link in links]
    return content_urls


def fetch_content_selenium(content_urls):
    mobile_post_list = []
    for url in content_urls:
        driver = webdriver.Chrome('/usr/local/bin/chromedriver')
        driver.get(url)
        # 等待網頁載入
        driver.implicitly_wait(15)  # seconds
        html = driver.page_source
        soup = BeautifulSoup(html)
        # pprint(soup)

        author = soup.find("a", class_="u-ellipsis").getText().replace("\n", "")
        title = soup.find("h1", class_="t2").getText()
        create_time = soup.find("span", class_="o-fNotes").getText()


        # print(author, title, create_time)
        try:
            content = soup.find("div", itemprop="articleBody").getText()
            # print(content)

            pre_all_response_list = [content.string for content in soup.find_all("article")]
            # print(pre_all_response_list)

            all_response_list = [content.replace("\n", "") for content in pre_all_response_list if content]
        except:
            continue
        else:
            mobile_post = {'author': author,
                           'title': title,
                           'create_time': create_time,
                           'content': content,
                           'all_response_list': all_response_list}

            mobile_post_list.append(mobile_post)
            time.sleep(0.5)
    return mobile_post_list

for i in range(3):
    content_urls = fetch_content_url_selenium(i)
    print(content_urls)
    mobile_post_list = fetch_content_selenium(content_urls)

    db_mongo = model_mongo.DbWrapperMongo()
    collection = "mobile01"
    db_mongo.insert_many(collection, mobile_post_list)
    time.sleep(0.5)