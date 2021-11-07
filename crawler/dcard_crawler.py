import time
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta

HEADERS = {
    'Cookie': '__cf_bm=BKHIhP4lrP5ixa6SbmyKTENoYnytlnWKEMLuW2Ze7DE-1634548207-0-AbcAn0IJ6uIOxDkAUgUsrJNtqLuwGE39PDiIKLBHt8IxFTsfrBYFWcyJ0/0thONONbdmMh88twDPIs2BeStNjtI=; _fbp=fb.1.1634173200753.494800038; _ga=GA1.2.987194377.1634173200; _gid=GA1.2.1845398910.1634547889; __asc=ca49bf3717c92a56f876ee59770; __auc=6068bd4c17c7c5025fda41c083c; _ga_C3J49QFLW7=GS1.1.1634547887.3.1.1634548206.0; _gat=1',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'www.dcard.tw',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Accept-Language': 'zh-tw',
    'Referer': 'https://www.dcard.tw/f/stock?latest=true',
    'Connection': 'keep-alive',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': "macOS",
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

cookie_dict = {
    "__asc": "__ascca49bf3717c92a56f876ee59770,",
    "__auc": "__auc6068bd4c17c7c5025fda41c083c",
    "__cf_bm": "BKHIhP4lrP5ixa6SbmyKTENoYnytlnWKEMLuW2Ze7DE-1634548207-0-AbcAn0IJ6uIOxDkAUgUsrJNtqLuwGE39PDiIKLBHt8IxFTsfrBYFWcyJ0/0thONONbdmMh88twDPIs2BeStNjtI=",
    "_fbp": "fb.1.1634173200753.494800038",
    "_ga": "GA1.2.987194377.1634173200",
    "_ga_C3J49QFLW7": "GS1.1.1634547887.3.1.1634548206.0",
    "_gat": "1",
    "_gid": "GA1.2.1845398910.1634547889"
}



def fetch_content(post_id):
    post_url = 'https://www.dcard.tw/f/stock/p/' + post_id  # 將 id 加到網址後
    r = requests.get(post_url, headers=HEADERS, cookies=cookie_dict)
    if r.status_code != requests.codes.ok:
        print(r.status_code)  # 如果文章被刪會跳 404 (或 ip 被 ban)
        # raise SystemExit  # 結束程式(希望能繼續爬)

    soup = BeautifulSoup(r.text, 'html.parser')

    # 關鍵資訊以JSON形式存於這個script tag，因此抓取
    script = soup.find('script', id='__NEXT_DATA__')  # 該段 json 包含所有資料應該是類似 callback 方式取得
    d = json.loads(script.string)  # 把取出的JSON形式字串轉換回字典以方便操作
    # pprint(d) # 建議先執行此行，看看整個資料結構總共有哪些東西 (底下圖1為輸出範例的區域截圖)

    try:
        post_data = d['props']['initialState']['post']['data'][post_id]  # 這是文章資訊在所有資料中的位置

    except:  # 如果作者不存在
        print('遇到被刪除的貼文 跳過就好 否則會存取不到like_count等其他資訊 會出錯')
    else:
        articleID = post_data['id']  # 貼文 id
        author = post_data['school']  # 作者
        forum_alias = post_data['forumAlias']  # 論壇名稱
        created_at_utc = datetime.fromisoformat(
            post_data['createdAt'].split('Z')[0])  # type datetime.datetime 建立時間 (2021-08-06 09:54:46.599000) 取出來記得時區+8
        created_at_tw = created_at_utc + timedelta(hours=+8)  # type datetime.datetime 建立時間 (2021-08-06 17:54:46.599000)
        time_string = post_data['timeString']  # 時間字串
        title = post_data['title']  # 文章標題
        topics = '/'.join([str(topic) for topic in post_data['topics']])  # 文章主題
        content = post_data['content']  # 文章內容
        gender = post_data["gender"]  # 作者性別
        react_count = post_data['reactionCount']  # 心情數 = like_count
        comment_count = post_data['commentCount']  # 留言數

    ############### 開始爬取留言 #####################

    # 先取得留言數
    comment_count = d['props']['initialState']['post']['data'][post_id]['commentCount']
    print(f'total comment count = {comment_count}')

    success = 0  # debug 檢查使用
    for i in range(1, comment_count + 1):
        comment_url = post_url + '/b/' + str(i)
        r = requests.get(comment_url)
        if r.status_code != requests.codes.ok:
            continue  # 如存取不順，跳過 (跳過有風險，剛開始應該直接中斷程式測試穩定後再改成繼續)

        soup = BeautifulSoup(r.text, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        d = json.loads(script.string)

        reaction_id = post_id + '-' + str(i)
        comment_id = d['props']['initialState']['comment']['doorplateMap'][reaction_id]
        comment_data = d['props']['initialState']['comment']['data'][comment_id]
        # pprint(comment_data) # 可先執行這行了解每則留言有哪些資料訊息

        try:
            author = comment_data['school']  # 如果沒資料就跳過
        except:
            print('遇到被刪除的留言 跳過就好 否則會存取不到like_count等其他資訊 會出錯')
            continue  # 省略下半部

        reactionID = reaction_id
        articleID = comment_data['postId']
        created_at_utc = datetime.fromisoformat(comment_data['createdAt'].split('Z')[0])
        created_at_tw = created_at_utc + timedelta(hours=+8)
        like_count = comment_data['likeCount']
        content = comment_data['content']

        success += 1

    print('success = ', success)  # debug 檢查總共拿了幾個留言，看跟上面取到的留言數一不一樣

def fetch_content_url_selenium(before_id=None):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("window-size=1400,1500")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")

    # driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=options)
    # on EC2
    driver = webdriver.Chrome(options=options)

    if before_id:
        driver.get(f"https://www.dcard.tw/service/api/v2/forums/stock/posts?popular=false&limit=100&before={before_id}")
    else:
        driver.get("https://www.dcard.tw/service/api/v2/forums/stock/posts?limit=100")
    # 等待網頁載入
    print('success')
    driver.implicitly_wait(30)  # seconds
    time.sleep(1)
    html = driver.page_source
    print('get html')
    soup = BeautifulSoup(html, features='lxml')
    print(soup)
    json_dict = json.loads(str(soup.text))
    # pprint(json_dict)
    id_list = [_id['id'] for _id in json_dict]
    return id_list

# def fetch_content_url(before_id=None):
#     if before_id:
#         url = f"https://www.dcard.tw/service/api/v2/forums/stock/posts?popular=false&limit=100&before={before_id}"
#     else:
#         url = "https://www.dcard.tw/service/api/v2/forums/stock/posts?popular=false&limit=100"
#     # 等待網頁載入
#     r = requests.get(url, headers=HEADERS)
#     json_str = r.text
#     json_data = json.loads(json_str)
#     return json_data

id_list = fetch_content_url_selenium()
print(id_list)
before_id = id_list[-1]
print(before_id)

# json_data = fetch_content_url()
# print(json_data)