# import package
from datetime import date
from urllib.request import urlopen
from dateutil import rrule
import datetime
import pandas as pd
import json
import time
import requests
from bs4 import BeautifulSoup
import re
import model_mysql


# 爬取每月股價的目標網站並包裝成函式
def craw_one_month(stock_number,date):
    url = "http://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=" + date.strftime('%Y%m%d') + "&stockNo=" + str(stock_number)
    data = json.loads(urlopen(url).read())
    return pd.DataFrame(data['data'],columns=data['fields'])


# 根據使用者輸入的日期，以月為單位，重複呼叫爬取月股價的函式
def craw_stock(stock_number, start_month):
    b_month = date(*[int(x) for x in start_month.split('-')])
    now = datetime.datetime.now().strftime("%Y-%m-%d")  # 取得現在時間
    e_month = date(*[int(x) for x in now.split('-')])

    result = pd.DataFrame()
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=b_month, until=e_month):
        result = pd.concat([result, craw_one_month(stock_number, dt)], ignore_index=True)
        time.sleep(5000.0 / 1000.0)

    return result


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
    # pprint(soup.prettify())
    a_tags = soup.find_all("a", href=re.compile(r'javascript:setid'))
    # print(a_tags)
    stock_code_names = [stock_code_name.get('href').split("'") for stock_code_name in a_tags]
    # print(stock_code_names)
    stock_code_name_dict_list = [{'stock_code': stock_code_name[1], 'stock_name': stock_code_name[3]} for stock_code_name in stock_code_names]
    # print(stock_code_name_dict_list)
    stock_code_list = [stock_code_name_dict['stock_code'] for stock_code_name_dict in stock_code_name_dict_list]
    # print(stock_code_list)
    stock_name_list = [stock_code_name_dict['stock_name'] for stock_code_name_dict in stock_code_name_dict_list]
    # print(stock_name_list)

    return stock_code_name_dict_list, stock_code_list, stock_name_list

# fetch_stock_list
# stock_kind_list = ['電腦週邊', '光電', '通訊網路', '電子零組件', '電子通路', '資訊服務', '其他電子', '航運', '生技', '金融業']
# all_stock_name_list = []
# all_stock_code_list = []
# for stock_kind in stock_kind_list:
#     stock_code_name_dict_list, stock_code_list, stock_name_list = fetch_stock_list(stock_kind)
#     # print(stock_code_name_dict_list)
#     # print(stock_code_list)
#     for stock_name in stock_name_list:
#         all_stock_name_list.append(stock_name)
#     for stock_code in stock_code_list:
#         all_stock_code_list.append(stock_code)
#     time.sleep(1)
#
# # print(all_stock_name_list)
# for stock_name in all_stock_name_list:
#     print(f"{stock_name} 1 N")
#
# # print(all_stock_code_list)
# for stock_code in all_stock_code_list:
#     print(f"{stock_code} 1 N")

# fetch from mysql
db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
sql_fetch_list = "SELECT * FROM stocks where category = 'electric_car' AND stock_code <> 1;"
result = db_mysql.query_tb_all(sql_fetch_list)
electric_car_stock_list = [stock_tuple[0] for stock_tuple in result]
print(electric_car_stock_list)

# 航運、電子、金融、生技
# 電腦週邊
computer_stock_list = ['2301', '2305', '2324', '2331', '2352', '2353', '2356', '2357', '2362', '2364', '2365', '2376', '2377', '2380', '2382', '2387', '2395', '2397', '2399', '2405', '2417', '2424', '2425', '2442', '2465', '3002', '3005', '3013', '3017', '3022', '3046', '3057', '3060', '3231', '3416', '3494', '3515', '3701', '3706', '3712', '4916', '4938', '5215', '5258', '6117', '6128', '6166', '6172', '6206', '6230', '6235', '6277', '6414', '6579', '6591', '6669', '8114', '8163', '8210', '9912']
# 光電
light_eletric_stock_list = ['2323', '2340', '2349', '2374', '2393', '2406', '2409', '2426', '2429', '2438', '2466', '2486', '2489', '2491', '3008', '3019', '3024', '3031', '3038', '3049', '3050', '3051', '3059', '3149', '3356', '3383', '3406', '3437', '3454', '3481', '3504', '3535', '3543', '3563', '3576', '3591', '3622', '3673', '3714', '4934', '4935', '4942', '4956', '4960', '4976', '5234', '5243', '5484', '6116', '6120', '6164', '6168', '6176', '6209', '6225', '6226', '6278', '6289', '6405', '6431', '6443', '6456', '6477', '6668', '6706', '8104', '8105', '8215']
# 通訊網路
internet_stock_list = ['2314', '2321', '2332', '2345', '2412', '2419', '2439', '2444', '2450', '2455', '2485', '2498', '3025', '3027', '3045', '3047', '3062', '3138', '3311', '3380', '3419', '3596', '3669', '3682', '3694', '3704', '4904', '4906', '4977', '5388', '6136', '6142', '6152', '6216', '6285', '6416', '6426', '6442', '6674', '8011', '8101']
# 電子零組件
component_stock_list = ['1471', '1582', '2059', '2308', '2313', '2316', '2327', '2328', '2355', '2367', '2368', '2375', '2383', '2385', '2392', '2402', '2413', '2415', '2420', '2421', '2428', '2431', '2440', '2456', '2457', '2460', '2462', '2467', '2472', '2476', '2478', '2483', '2484', '2492', '2493', '3003', '3011', '3015', '3021', '3023', '3026', '3032', '3037', '3042', '3044', '3058', '3090', '3092', '3229', '3296', '3308', '3321', '3338', '3376', '3432', '3501', '3533', '3550', '3593', '3605', '3607', '3645', '3653', '3679', '4545', '4912', '4915', '4927', '4943', '4958', '4989', '4999', '5469', '6108', '6115', '6133', '6141', '6153', '6155', '6191', '6197', '6205', '6213', '6224', '6251', '6269', '6282', '6412', '6449', '6672', '6715', '6781', '8039', '8046', '8103', '8213', '8249']
# 電子通路
pathway_stock_list = ['2347', '2414', '2430', '3010', '3028', '3033', '3036', '3036A', '3048', '3055', '3209', '3312', '3528', '3702', '3702A', '5434', '6189', '6281', '6776', '8070', '8072', '8112']
# 資訊服務
it_stock_list = ['2427', '2453', '2468', '2471', '2480', '3029', '3130', '4994', '5203', '6112', '6183', '6214']
# 其他電子
other_electric_stock_list = ['2312', '2317', '2354', '2359', '2360', '2373', '2390', '2404', '2423', '2433', '2459', '2461', '2464', '2474', '2477', '2482', '2488', '2495', '3018', '3030', '3043', '3305', '3518', '3617', '3665', '5225', '6139', '6192', '6196', '6201', '6215', '6283', '6409', '6438', '6558', '6698', '6743', '8021', '8201', '8499']
# 航運
sail_stock_list = ['2208', '2603', '2605', '2606', '2607', '2608', '2609', '2610', '2611', '2612', '2613', '2615', '2617', '2618', '2630', '2633', '2634', '2636', '2637', '2642', '5607', '5608', '8367']
# 生技
bio_stock_list = ['1598', '1701', '1707', '1720', '1731', '1733', '1734', '1736', '1760', '1762', '1783', '1786', '1789', '1795', '3164', '3705', '4104', '4106', '4108', '4119', '4133', '4137', '4141', '4142', '4148', '4155', '4164', '4190', '4737', '4746', '6491', '6541', '6598', '6666']
# 金融
finance_stock_list = ['2801', '2809', '2812', '2816', '2820', '2823', '2832', '2834', '2836', '2836A', '2838', '2838A', '2845', '2849', '2850', '2851', '2852', '2855', '2867', '2880', '2881', '2881A', '2881B', '2882', '2882A', '2882B', '2883', '2884', '2885', '2886', '2887', '2887E', '2887F', '2888', '2888A', '2888B', '2889', '2890', '2891', '2891B', '2891C', '2892', '2897', '2897A', '5876', '5880', '6005', '6024']




