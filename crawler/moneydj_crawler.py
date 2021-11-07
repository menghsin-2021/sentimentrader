import requests
from bs4 import BeautifulSoup
import model_mongo
import time

HEADERS = {
    'Cookie': 'quads_browser_width=1920; quads_browser_width=1920; __asc=e99e9b0717c8d8075ba97aa8b76; __auc=1db1816e17c887493e17dbaaea0; _ga=GA1.2.321410263.1634376914; _gid=GA1.2.704556416.1634376914; PHPSESSID=u6tfc9fu5lj2r2lluard5uuo82; _fbp=fb.1.1634376914051.1026372353; djaid=1.1a09e0ea-3ce3-483d-8566-ce81834aa80c.1634376913.1039206186.0.0.8ad0d; mp_5d993f8d7d28ac292101f3a9d1b56721_mixpanel=%7B%22distinct_id%22%3A%20%2217c887493e6d3f-0715ac3ae2ae138-3e62684b-232800-17c887493e726cd%22%2C%22%24device_id%22%3A%20%2217c887493e6d3f-0715ac3ae2ae138-3e62684b-232800-17c887493e726cd%22%2C%22utm_source%22%3A%20%2296963757966759579618573737%22%2C%22utm_medium%22%3A%20%22RSS%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.cmoney.tw%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.cmoney.tw%22%7D',
    'Host': 'blog.moneydj.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-tw',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

def fetch_content_url(page):
    list_url = f"https://blog.moneydj.com/news/category/來源/moneydj/page/{page}/"
    print("URL:", list_url)
    # try:
    r = requests.get(list_url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    # pprint(soup.prettify())
    link_titles = soup.find_all("h3", class_='entry-title')
    # pprint(link_titles)
    a = [link_title.findChildren()[0] for link_title in link_titles]
    # pprint(a)
    content_urls = [link.get('href') for link in a]
    return content_urls

def fetch_content(content_urls):
    url = content_urls[0]
    print("URL:", url)
    # try:
    r = requests.get(url, headers=HEADERS)
    web_content = r.text
    soup = BeautifulSoup(web_content, 'html.parser')
    title = soup.find("h1", class_="entry-title").getText()
    create_time = soup.find("span", class_="entry-meta-date").getText()
    # print(title, create_time)

    ## 查找所有html 元素 抓出內容
    main_container = soup.find("div", class_="entry-content")
    # 把所有文字都抓出來
    content = main_container.text
    # print(content)
    return title, create_time, content

def fetch_content_page(content_urls):
    moneydj_post_list = []
    for url in content_urls:
        # print("URL:", url)
        try:
            r = requests.get(url, headers=HEADERS)
            web_content = r.text
            soup = BeautifulSoup(web_content, 'html.parser')
            title = soup.find("h1", class_="entry-title").getText()
            create_time = soup.find("span", class_="entry-meta-date").getText()
            # print(title, create_time)

            ## 查找所有html 元素 抓出內容
            main_container = soup.find("div", class_="entry-content")
            # 把所有文字都抓出來
            content = main_container.text
            # print(content)

        except:
            continue

        else:
            moneydj_post = {'title': title,
                            'create_time': create_time,
                            'content': content}
            moneydj_post_list.append(moneydj_post)
            time.sleep(0.5)

    return moneydj_post_list




if __name__ == '__main__':
    for i in range(1, 2505):  # 10/18 back
        try:
            content_urls = fetch_content_url(i)
            # print(content_urls)

            # fetch page
            moneydj_post_list = fetch_content_page(content_urls)

        except:
            continue

        else:
            db_mongo = model_mongo.DbWrapperMongo()
            col_name = "moneydj"
            db_mongo.insert_many(col_name, moneydj_post_list)
            time.sleep(0.5)
