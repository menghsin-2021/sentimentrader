from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import time
from sqlalchemy import create_engine
import sqlalchemy
from bs4 import BeautifulSoup
from selenium import webdriver
import config

from selenium.webdriver.chrome.options import Options
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

def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d') + 'T00:00:00.000+00:00'

    timestamp_today = int(datetime.fromisoformat(today_strftime).timestamp())
    timestamp_day_before = int((datetime.fromisoformat(today_strftime) - timedelta(days=2)).timestamp())  # for 自動化
    # timestamp_day_before_check = int(datetime.fromisoformat('2021-11-01T00:00:00.000+00:00').timestamp())
    print(timestamp_today)
    print(timestamp_day_before)
    # print(timestamp_day_before_check)
    # timestamp_end = 1635811200  # 2021/11/02 00:00:00
    # timestamp_start = 1634947200  # 2021/10/23 00:00:00
    return timestamp_day_before, timestamp_today

def craw_stock(stock_code, timestamp_start, timestamp_end):
    TWO = [1599, 2237, 4503, 4721, 4738, 5227, 5233, 5439, 6121, 6275, 8038, 8109, 8171, 8183, 8358, 8933, 8937]
    # 網址
    if stock_code not in TWO:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW?period1={timestamp_start}&period2={timestamp_end}&interval=1d&events=history&=hP2rOschxO0"
    else:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TWO?period1={timestamp_start}&period2={timestamp_end}&interval=1d&events=history&=hP2rOschxO0"
    driver = webdriver.Chrome('/usr/local/bin/chromedriver')
    # driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)
    driver.get(url)
    # 等待網頁載入
    driver.implicitly_wait(15)  # seconds
    html = driver.page_source
    soup = BeautifulSoup(html)
    data = json.loads(soup.text)
    # print(data)
    df = pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0],
                      index=pd.to_datetime(np.array(data['chart']['result'][0]['timestamp']) * 1000 * 1000 * 1000))

    df['stock_code'] = stock_code
    driver.quit()
    return df


# 將整個 dataframe 存入 (這裡只能用 sqlalchemy)
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
# 電動車
electric_car_stock_list = ['1503', '1519', '1533', '1536', '1537', '1587', '1599', '1611', '1723', '2237', '2371', '4503', '4721', '4738', '4739', '5227', '5233', '5439', '6121', '6275', '8038', '8109', '8171', '8183', '8358', '8933', '8937', '9914']
# 2330
stock_market_list = ['2330']

all_list = [computer_stock_list, light_eletric_stock_list, internet_stock_list, component_stock_list, pathway_stock_list,
            it_stock_list, other_electric_stock_list, sail_stock_list, bio_stock_list, finance_stock_list, stock_market_list]
# 自動化記得加 stock_market_list

timestamp_day_before, timestamp_today = get_today()

# for list in all_list:
#     for stock_code in list:
#         try:
#             df = craw_stock(stock_code, timestamp_day_before, timestamp_today)
#             # print(df)
#             df_row_insert(df)
#             time.sleep(1)
#
#         except:
#             print(f"{stock_code} fail")
#             continue

stock_fail = [3046, 3051]
for stock_code in stock_fail:
    try:
        df = craw_stock(stock_code, timestamp_day_before, timestamp_today)
        # print(df)
        df_row_insert(df)
        time.sleep(1)
    except:
        print(f"{stock_code} fail")
        stock_fail.append(stock_code)
        continue

print(stock_fail)


# stock fail
# stock_fail = ['6442', '2887F', '2491', '8249']
# stock_fail = ['2887F']
# stock_fail_2 = []
# for stock_code in stock_fail:
#     try:
#         df = craw_stock(stock_code, 0, timestamp_end)
#         df_row_insert(df)
#         time.sleep(1)
#     except:
#         print(f"{stock_code} fail")
#         stock_fail_2.append(stock_code)
#         continue
#
# print(stock_fail_2)



# df = craw_stock(2330,timestamp_start, timestamp_end)
# df_row_insert(df)

# 6442 fail
# 2887F fail
# 2491 fail
# 8249 fail