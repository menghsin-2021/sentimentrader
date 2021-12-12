import requests
import time
import json
from datetime import datetime
from lxml import etree
import csv
import urllib3
import model_mongo

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362',
}


def get_today_tomorrow():
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    today_strftime = today.strftime('%Y-%m-%d')
    tomorrow_strftime = tomorrow.strftime('%Y-%m-%d')

    return today_strftime, tomorrow_strftime


# save data as CSV file
def savefile(beginday, stopday, news):
    filename = 'cnyes-' + beginday + '~' + stopday + '.csv'
    with open(filename, 'a', newline='', encoding='utf8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(news)


def savemongo(news):
    db_mongo = model_mongo.DbWrapperMongo()
    cnyes_post = {'date': news[0],
                    'time': news[1],
                    'title': news[2],
                    'tag': news[3],
                    'content': news[4],
                    'url': news[5]}
    db_mongo.insert_one("cnyes", cnyes_post)
    # db_mongo.insert_one("test", cnyes_post)


def parse(headers, newsID, k, total, beginday, stopday):
    fnews_url = 'https://news.cnyes.com/news/id/{}?exp=a'.format(newsID)  # 原始新聞網址
    response = requests.get(fnews_url, headers)
    html = etree.HTML(response.content)
    try:
        title = html.xpath('//*[@id="content"]/div/div/div[2]/main/div[2]/h1/text()')[0]  # 新聞標題
        print('第 {} / {} 篇新聞: '.format(k, total), title)
        posttime = html.xpath('//*[@id="content"]/div/div/div[2]/main/div[2]/div[2]/time/text()')[0]
        posttime = posttime.split(' ')
        date = posttime[0]  # 新聞發佈日期
        time = posttime[1]  # 新聞發佈時間
        content = html.xpath('//*[@id="content"]/div/div/div[2]/main/div[3]/article/section[1]/div[2]/div[1]//text()')
        content = ''.join(content).strip()  # 新聞內文
        content = content.replace('\n', '')
        url = fnews_url.replace('?exp=a', '')  # 原始新聞來源網址
        tag = html.xpath('//*[@id="content"]/div/div/div[2]/main/div[3]/article/section[1]/nav/a[1]/span//text()')
        tag = ','.join(tag).strip()  # Tag
        news = [date, time, title, tag, content, url]
        print("news:",news)
        # save data to mongodb
        savemongo(news)

    except IndexError as IE:
        print('抓值範圍錯誤')
        print('html:', response.text)
        news = {"title": None, "date": None, "content": None, "url": None, "tag": None}
    except OSError as OSErr:
        print('OSError:{}'.format(OSErr))
    except requests.exceptions.ConnectionError as REC:
        print('連線錯誤')
    except urllib3.exceptions.ProtocolError as UEP:
        print('連線錯誤')
    return news


# get the number of news
def crawler(beginday, stopday):
    # search start date 'Y-M-D'
    be_day = beginday
    # search end date
    st_day = stopday
    # change time format
    startday = int(datetime.timestamp(datetime.strptime(be_day, "%Y-%m-%d")))
    endday = int(datetime.timestamp(datetime.strptime(st_day, "%Y-%m-%d")) - 1)
    url = 'https://news.cnyes.com/api/v3/news/category/tw_stock?startAt={}&endAt={}&limit=30'.format(startday, endday)
    print(url)
    res = requests.get(url, headers)

    newsID_lt = []
    # total page
    last_page = json.loads(res.text)['items']['last_page']
    print('總共 {} 頁'.format(last_page))
    # select newsId
    newsIDlist = json.loads(res.text)['items']['data']

    # get the first newsId
    for i in newsIDlist:
        newsID = i['newsId']
        newsID_lt.append(newsID)
    print('正在獲取第 1 頁 newsId')
    time.sleep(1)

    # find the newsId in every page
    for p in range(2, last_page + 1):
        oth_url = 'https://news.cnyes.com/api/v3/news/category/tw_stock?startAt={}&endAt={}&limit=30&page={}'.format(
            startday, endday, p)
        res = requests.get(oth_url, headers)
        print('正在獲取第 {} 頁 newsId'.format(p))
        # get newsId
        newsIDlist = json.loads(res.text)['items']['data']
        for j in newsIDlist:
            newsID = j['newsId']
            newsID_lt.append(newsID)
        # time sleep
        time.sleep(1)

    # get news from newId
    for k, n in enumerate(newsID_lt):
        data = parse(headers, n, k + 1, len(newsID_lt), beginday, stopday)
        # time sleep
        time.sleep(0.5)


def main(beginyear, beginmonth, crawlrange, stopmonth=12):
    # get news before 15th and after 16th
    if crawlrange == 1:
        # before 15th
        for m in range(beginmonth, stopmonth + 1):
            if m < 10:
                beginday = '{}-0{}-01'.format(beginyear, m)
                stopday = '{}-0{}-16'.format(beginyear, m)
            else:
                beginday = '{}-{}-01'.format(beginyear, m)
                stopday = '{}-{}-16'.format(beginyear, m)
            crawler(beginday, stopday)
            if m == 12:
                print('程式執行完成')
                break
            # else:
            # print('切換到 {} 月份等待5秒'.format(m+1))
            time.sleep(5)

    elif crawlrange == 2:
        # after 16th
        for m in range(beginmonth, stopmonth + 1):
            beginday = '{}-0{}-16'.format(beginyear, m)
            if m == 9:
                stopday = '{}-{}-01'.format(beginyear, m + 1)
            elif m >= 10:
                beginday = '{}-{}-16'.format(beginyear, m)
                if m == 12:
                    stopday = '{}-01-01'.format(beginyear + 1)
                else:
                    stopday = '{}-{}-01'.format(beginyear, m + 1)
            else:
                stopday = '{}-0{}-01'.format(beginyear, m + 1)

            crawler(beginday, stopday)
            if m == stopmonth:
                print('程式執行完成')
                break
            # else:
            # print('change to {} and wait 5 secs'.format(m+1))
            time.sleep(5)
    else:
        print('爬取區間設定錯誤!')


if __name__ == '__main__':
    beginyear = 2021  # 爬取新聞年份  最早2010
    beginmonth = 10  # 爬取新聞開始月份
    stopmonth = 10  # 爬取停止月份

    # 爬取月份區間,因為測試直接抓一整個月伺服器回傳的資訊可能會出現異常,
    # 所以分成上半月(1~15日)和下半月(16~月底)
    for i in range(2021, 2020, -1):
        for j in range(1, 3):  # 先爬上半月再爬下半月
            main(i, beginmonth, j, stopmonth)

    # main(beginyear, 10, 2, 10)


# fetch {date: {$gt: "2017/01/16", $lt:"2017/01/32"}}
# delete db.cnyes.deleteMany({date: {$gt: "2017/01/16", $lt:"2017/01/32"}})