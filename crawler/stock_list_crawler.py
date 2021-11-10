# # import package
# from datetime import date
# from urllib.request import urlopen
# from dateutil import rrule
# import datetime
# import pandas as pd
# import json
# import time
# import requests
# from bs4 import BeautifulSoup
# import re
# import model_mysql
#
#
# # 爬取每月股價的目標網站並包裝成函式
# def craw_one_month(stock_number,date):
#     url = "http://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=" + date.strftime('%Y%m%d') + "&stockNo=" + str(stock_number)
#     data = json.loads(urlopen(url).read())
#     return pd.DataFrame(data['data'],columns=data['fields'])
#
#
# # 根據使用者輸入的日期，以月為單位，重複呼叫爬取月股價的函式
# def craw_stock(stock_number, start_month):
#     b_month = date(*[int(x) for x in start_month.split('-')])
#     now = datetime.datetime.now().strftime("%Y-%m-%d")  # 取得現在時間
#     e_month = date(*[int(x) for x in now.split('-')])
#
#     result = pd.DataFrame()
#     for dt in rrule.rrule(rrule.MONTHLY, dtstart=b_month, until=e_month):
#         result = pd.concat([result, craw_one_month(stock_number, dt)], ignore_index=True)
#         time.sleep(5000.0 / 1000.0)
#
#     return result
#
#
# def fetch_stock_list(kind):
#     url = f"https://tw.stock.yahoo.com/h/kimosel.php?tse=1&cat={kind}&form=menu&form_id=stock_id&form_name=stock_name&domain=0"
#
#     headers = {
#         'Cookie': 'A1=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko; A1S=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko&j=WORLD; A3=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko; B=5k8ksa5gmsahv&b=3&s=qd; GUC=AQEBAQFhb35heEIfngTT; cmp=t=1634610354&j=0; A1S=d=AQABBKksbmECELy9KyV-cyoPGc4o8MS2UawFEgEBAQF-b2F4YQAAAAAA_eMAAAcIPypuYVGcIlo&S=AQAAAhxc_XunubCL2X8fCqtG6ko&j=US',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Host': 'tw.stock.yahoo.com',
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
#         'Accept-Language': 'zh-tw',
#         'Referer': 'https://tw.stock.yahoo.com/h/kimosel.php?tse=1&cat=%E9%9B%BB%E8%85%A6%E9%80%B1%E9%82%8A&form=menu&form_id=stock_id&form_name=stock_name&domain=0',
#         'Connection': 'keep-alive'
#     }
#
#     resp = requests.request("GET", url, headers=headers)
#     web_content = resp.text
#     soup = BeautifulSoup(web_content, 'html.parser')
#     # pprint(soup.prettify())
#     a_tags = soup.find_all("a", href=re.compile(r'javascript:setid'))
#     # print(a_tags)
#     stock_code_names = [stock_code_name.get('href').split("'") for stock_code_name in a_tags]
#     # print(stock_code_names)
#     stock_code_name_dict_list = [{'stock_code': stock_code_name[1], 'stock_name': stock_code_name[3]} for stock_code_name in stock_code_names]
#     # print(stock_code_name_dict_list)
#     stock_code_list = [stock_code_name_dict['stock_code'] for stock_code_name_dict in stock_code_name_dict_list]
#     # print(stock_code_list)
#     stock_name_list = [stock_code_name_dict['stock_name'] for stock_code_name_dict in stock_code_name_dict_list]
#     # print(stock_name_list)
#
#     return stock_code_name_dict_list, stock_code_list, stock_name_list
#
# # fetch_stock_list
# # stock_kind_list = ['電腦週邊', '光電', '通訊網路', '電子零組件', '電子通路', '資訊服務', '其他電子', '航運', '生技', '金融業']
# # all_stock_name_list = []
# # all_stock_code_list = []
# # for stock_kind in stock_kind_list:
# #     stock_code_name_dict_list, stock_code_list, stock_name_list = fetch_stock_list(stock_kind)
# #     # print(stock_code_name_dict_list)
# #     # print(stock_code_list)
# #     for stock_name in stock_name_list:
# #         all_stock_name_list.append(stock_name)
# #     for stock_code in stock_code_list:
# #         all_stock_code_list.append(stock_code)
# #     time.sleep(1)
# #
# # # print(all_stock_name_list)
# # for stock_name in all_stock_name_list:
# #     print(f"{stock_name} 1 N")
# #
# # # print(all_stock_code_list)
# # for stock_code in all_stock_code_list:
# #     print(f"{stock_code} 1 N")
#
# # fetch from mysql
# db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
# sql_fetch_list = "SELECT * FROM stocks where category = 'electric_car' AND stock_code <> 1;"
# result = db_mysql.query_tb_all(sql_fetch_list)
# electric_car_stock_list = [stock_tuple[0] for stock_tuple in result]
# print(electric_car_stock_list)
#
# # 航運、電子、金融、生技
# # 電腦週邊
# computer_stock_list = ['2301', '2305', '2324', '2331', '2352', '2353', '2356', '2357', '2362', '2364', '2365', '2376', '2377', '2380', '2382', '2387', '2395', '2397', '2399', '2405', '2417', '2424', '2425', '2442', '2465', '3002', '3005', '3013', '3017', '3022', '3046', '3057', '3060', '3231', '3416', '3494', '3515', '3701', '3706', '3712', '4916', '4938', '5215', '5258', '6117', '6128', '6166', '6172', '6206', '6230', '6235', '6277', '6414', '6579', '6591', '6669', '8114', '8163', '8210', '9912']
# # 光電
# light_eletric_stock_list = ['2323', '2340', '2349', '2374', '2393', '2406', '2409', '2426', '2429', '2438', '2466', '2486', '2489', '2491', '3008', '3019', '3024', '3031', '3038', '3049', '3050', '3051', '3059', '3149', '3356', '3383', '3406', '3437', '3454', '3481', '3504', '3535', '3543', '3563', '3576', '3591', '3622', '3673', '3714', '4934', '4935', '4942', '4956', '4960', '4976', '5234', '5243', '5484', '6116', '6120', '6164', '6168', '6176', '6209', '6225', '6226', '6278', '6289', '6405', '6431', '6443', '6456', '6477', '6668', '6706', '8104', '8105', '8215']
# # 通訊網路
# internet_stock_list = ['2314', '2321', '2332', '2345', '2412', '2419', '2439', '2444', '2450', '2455', '2485', '2498', '3025', '3027', '3045', '3047', '3062', '3138', '3311', '3380', '3419', '3596', '3669', '3682', '3694', '3704', '4904', '4906', '4977', '5388', '6136', '6142', '6152', '6216', '6285', '6416', '6426', '6442', '6674', '8011', '8101']
# # 電子零組件
# component_stock_list = ['1471', '1582', '2059', '2308', '2313', '2316', '2327', '2328', '2355', '2367', '2368', '2375', '2383', '2385', '2392', '2402', '2413', '2415', '2420', '2421', '2428', '2431', '2440', '2456', '2457', '2460', '2462', '2467', '2472', '2476', '2478', '2483', '2484', '2492', '2493', '3003', '3011', '3015', '3021', '3023', '3026', '3032', '3037', '3042', '3044', '3058', '3090', '3092', '3229', '3296', '3308', '3321', '3338', '3376', '3432', '3501', '3533', '3550', '3593', '3605', '3607', '3645', '3653', '3679', '4545', '4912', '4915', '4927', '4943', '4958', '4989', '4999', '5469', '6108', '6115', '6133', '6141', '6153', '6155', '6191', '6197', '6205', '6213', '6224', '6251', '6269', '6282', '6412', '6449', '6672', '6715', '6781', '8039', '8046', '8103', '8213', '8249']
# # 電子通路
# pathway_stock_list = ['2347', '2414', '2430', '3010', '3028', '3033', '3036', '3036A', '3048', '3055', '3209', '3312', '3528', '3702', '3702A', '5434', '6189', '6281', '6776', '8070', '8072', '8112']
# # 資訊服務
# it_stock_list = ['2427', '2453', '2468', '2471', '2480', '3029', '3130', '4994', '5203', '6112', '6183', '6214']
# # 其他電子
# other_electric_stock_list = ['2312', '2317', '2354', '2359', '2360', '2373', '2390', '2404', '2423', '2433', '2459', '2461', '2464', '2474', '2477', '2482', '2488', '2495', '3018', '3030', '3043', '3305', '3518', '3617', '3665', '5225', '6139', '6192', '6196', '6201', '6215', '6283', '6409', '6438', '6558', '6698', '6743', '8021', '8201', '8499']
# # 航運
# sail_stock_list = ['2208', '2603', '2605', '2606', '2607', '2608', '2609', '2610', '2611', '2612', '2613', '2615', '2617', '2618', '2630', '2633', '2634', '2636', '2637', '2642', '5607', '5608', '8367']
# # 生技
# bio_stock_list = ['1598', '1701', '1707', '1720', '1731', '1733', '1734', '1736', '1760', '1762', '1783', '1786', '1789', '1795', '3164', '3705', '4104', '4106', '4108', '4119', '4133', '4137', '4141', '4142', '4148', '4155', '4164', '4190', '4737', '4746', '6491', '6541', '6598', '6666']
# # 金融
# finance_stock_list = ['2801', '2809', '2812', '2816', '2820', '2823', '2832', '2834', '2836', '2836A', '2838', '2838A', '2845', '2849', '2850', '2851', '2852', '2855', '2867', '2880', '2881', '2881A', '2881B', '2882', '2882A', '2882B', '2883', '2884', '2885', '2886', '2887', '2887E', '2887F', '2888', '2888A', '2888B', '2889', '2890', '2891', '2891B', '2891C', '2892', '2897', '2897A', '5876', '5880', '6005', '6024']


stock_list_electric_car = [('1611', '中電', 'electric_car'), ('1723', '中碳', 'electric_car'), ('2308', '台達電', 'electric_car'), ('2371', '大同', 'electric_car'), ('4721', '美琪瑪', 'electric_car'), ('4738', '尚化', 'electric_car'), ('4739', '康普', 'electric_car'), ('4999', '鑫禾', 'electric_car'), ('5227', '立凱-KY', 'electric_car'), ('6443', '元晶', 'electric_car'), ('8038', '長園科', 'electric_car'), ('8358', '金居', 'electric_car'), ('1503', '士電', 'electric_car'), ('1519', '華城', 'electric_car'), ('1533', '車王電', 'electric_car'), ('1536', '和大', 'electric_car'), ('1537', '廣隆', 'electric_car'), ('1587', '吉茂', 'electric_car'), ('2301', '光寶科', 'electric_car'), ('2317', '鴻海', 'electric_car'), ('2357', '華碩', 'electric_car'), ('2392', '正崴', 'electric_car'), ('2421', '建準', 'electric_car'), ('2459', '敦吉', 'electric_car'), ('2483', '百容', 'electric_car'), ('3023', '信邦', 'electric_car'), ('3665', '貿聯-KY', 'electric_car'), ('4503', '金雨', 'electric_car'), ('5233', '有量', 'electric_car'), ('5439', '高技', 'electric_car'), ('6121', '新普', 'electric_car'), ('6275', '元山', 'electric_car'), ('6282', '康舒', 'electric_car'), ('8109', '博大', 'electric_car'), ('8171', '天宇', 'electric_car'), ('8183', '精星', 'electric_car'), ('1599', '宏佳騰', 'electric_car'), ('2237', '華德動能', 'electric_car'), ('8933', '愛地雅', 'electric_car'), ('8937', '合騏', 'electric_car'), ('9914', '美利達', 'electric_car')]
stock_list_electric = [('2301', '光寶科', 'electirc'), ('2305', '全友', 'electirc'), ('2324', '仁寶', 'electirc'), ('2331', '精英', 'electirc'), ('2352', '佳世達', 'electirc'), ('2353', '宏碁', 'electirc'), ('2356', '英業達', 'electirc'), ('2357', '華碩', 'electirc'), ('2362', '藍天', 'electirc'), ('2364', '倫飛', 'electirc'), ('2365', '昆盈', 'electirc'), ('2376', '技嘉', 'electirc'), ('2377', '微星', 'electirc'), ('2380', '虹光', 'electirc'), ('2382', '廣達', 'electirc'), ('2387', '精元', 'electirc'), ('2395', '研華', 'electirc'), ('2397', '友通', 'electirc'), ('2399', '映泰', 'electirc'), ('2405', '浩鑫', 'electirc'), ('2417', '圓剛', 'electirc'), ('2424', '隴華', 'electirc'), ('2425', '承啟', 'electirc'), ('2442', '新美齊', 'electirc'), ('2465', '麗臺', 'electirc'), ('3002', '歐格', 'electirc'), ('3005', '神基', 'electirc'), ('3013', '晟銘電', 'electirc'), ('3017', '奇鋐', 'electirc'), ('3022', '威強電', 'electirc'), ('3046', '建��', 'electirc'), ('3057', '喬鼎', 'electirc'), ('3060', '銘異', 'electirc'), ('3231', '緯創', 'electirc'), ('3416', '融程電', 'electirc'), ('3494', '誠研', 'electirc'), ('3515', '華擎', 'electirc'), ('3701', '大眾控', 'electirc'), ('3706', '神達', 'electirc'), ('3712', '永崴投控', 'electirc'), ('4916', '事欣科', 'electirc'), ('4938', '和碩', 'electirc'), ('5215', '科嘉-KY', 'electirc'), ('5258', '虹堡', 'electirc'), ('6117', '迎廣', 'electirc'), ('6128', '上福', 'electirc'), ('6166', '凌華', 'electirc'), ('6172', '互億', 'electirc'), ('6206', '飛捷', 'electirc'), ('6230', '尼得科超眾', 'electirc'), ('6235', '華孚', 'electirc'), ('6277', '宏正', 'electirc'), ('6414', '樺漢', 'electirc'), ('6579', '研揚', 'electirc'), ('6591', '動力-KY', 'electirc'), ('6669', '緯穎', 'electirc'), ('8114', '振樺電', 'electirc'), ('8163', '達方', 'electirc'), ('8210', '勤誠', 'electirc'), ('9912', '偉聯', 'electirc'), ('2323', '中環', 'electirc'), ('2340', '光磊', 'electirc'), ('2349', '錸德', 'electirc'), ('2374', '佳能', 'electirc'), ('2393', '億光', 'electirc'), ('2406', '國碩', 'electirc'), ('2409', '友達', 'electirc'), ('2426', '鼎元', 'electirc'), ('2429', '銘旺科', 'electirc'), ('2438', '翔耀', 'electirc'), ('2466', '冠西電', 'electirc'), ('2486', '一詮', 'electirc'), ('2489', '瑞軒', 'electirc'), ('2491', '吉祥全', 'electirc'), ('3008', '大立光', 'electirc'), ('3019', '亞光', 'electirc'), ('3024', '憶聲', 'electirc'), ('3031', '佰鴻', 'electirc'), ('3038', '全台', 'electirc'), ('3049', '和鑫', 'electirc'), ('3050', '鈺德', 'electirc'), ('3051', '力特', 'electirc'), ('3059', '華晶科', 'electirc'), ('3149', '正達', 'electirc'), ('3356', '奇偶', 'electirc'), ('3383', '新世紀', 'electirc'), ('3406', '玉晶光', 'electirc'), ('3437', '榮創', 'electirc'), ('3454', '晶睿', 'electirc'), ('3481', '群創', 'electirc'), ('3504', '揚明光', 'electirc'), ('3535', '晶彩科', 'electirc'), ('3543', '州巧', 'electirc'), ('3563', '牧德', 'electirc'), ('3576', '聯合再生', 'electirc'), ('3591', '艾笛森', 'electirc'), ('3622', '洋華', 'electirc'), ('3673', 'TPK-KY', 'electirc'), ('3714', '富采', 'electirc'), ('4934', '太極', 'electirc'), ('4935', '茂林-KY', 'electirc'), ('4942', '嘉彰', 'electirc'), ('4956', '光鋐', 'electirc'), ('4960', '誠美材', 'electirc'), ('4976', '佳凌', 'electirc'), ('5234', '達興材料', 'electirc'), ('5243', '乙盛-KY', 'electirc'), ('5484', '慧友', 'electirc'), ('6116', '彩晶', 'electirc'), ('6120', '達運', 'electirc'), ('6164', '華興', 'electirc'), ('6168', '宏齊', 'electirc'), ('6176', '瑞儀', 'electirc'), ('6209', '今國光', 'electirc'), ('6225', '天瀚', 'electirc'), ('6226', '光鼎', 'electirc'), ('6278', '台表科', 'electirc'), ('6289', '華上', 'electirc'), ('6405', '悅城', 'electirc'), ('6431', '光麗-KY', 'electirc'), ('6443', '元晶', 'electirc'), ('6456', 'GIS-KY', 'electirc'), ('6477', '安集', 'electirc'), ('6668', '中揚光', 'electirc'), ('6706', '惠特', 'electirc'), ('8104', '錸寶', 'electirc'), ('8105', '凌巨', 'electirc'), ('8215', '明基材', 'electirc'), ('2314', '台揚', 'electirc'), ('2321', '東訊', 'electirc'), ('2332', '友訊', 'electirc'), ('2345', '智邦', 'electirc'), ('2412', '中華電', 'electirc'), ('2419', '仲琦', 'electirc'), ('2439', '美律', 'electirc'), ('2444', '兆勁', 'electirc'), ('2450', '神腦', 'electirc'), ('2455', '全新', 'electirc'), ('2485', '兆赫', 'electirc'), ('2498', '宏達電', 'electirc'), ('3025', '星通', 'electirc'), ('3027', '盛達', 'electirc'), ('3045', '台灣大', 'electirc'), ('3047', '訊舟', 'electirc'), ('3062', '建漢', 'electirc'), ('3138', '耀登', 'electirc'), ('3311', '閎暉', 'electirc'), ('3380', '明泰', 'electirc'), ('3419', '譁裕', 'electirc'), ('3596', '智易', 'electirc'), ('3669', '圓展', 'electirc'), ('3682', '亞太電', 'electirc'), ('3694', '海華', 'electirc'), ('3704', '合勤控', 'electirc'), ('4904', '遠傳', 'electirc'), ('4906', '正文', 'electirc'), ('4977', '眾達-KY', 'electirc'), ('5388', '中磊', 'electirc'), ('6136', '富爾特', 'electirc'), ('6142', '友勁', 'electirc'), ('6152', '百一', 'electirc'), ('6216', '居易', 'electirc'), ('6285', '啟��', 'electirc'), ('6416', '瑞祺電通', 'electirc'), ('6426', '統新', 'electirc'), ('6442', '光聖', 'electirc'), ('6674', '鋐寶科技', 'electirc'), ('8011', '台通', 'electirc'), ('8101', '華冠', 'electirc'), ('1471', '首利', 'electirc'), ('1582', '信錦', 'electirc'), ('2059', '川湖', 'electirc'), ('2308', '台達電', 'electirc'), ('2313', '華通', 'electirc'), ('2316', '楠梓電', 'electirc'), ('2327', '國巨', 'electirc'), ('2328', '廣宇', 'electirc'), ('2355', '敬鵬', 'electirc'), ('2367', '燿華', 'electirc'), ('2368', '金像電', 'electirc'), ('2375', '凱美', 'electirc'), ('2383', '台光電', 'electirc'), ('2385', '群光', 'electirc'), ('2392', '正崴', 'electirc'), ('2402', '毅嘉', 'electirc'), ('2413', '環科', 'electirc'), ('2415', '錩新', 'electirc'), ('2420', '新巨', 'electirc'), ('2421', '建準', 'electirc'), ('2428', '興勤', 'electirc'), ('2431', '聯昌', 'electirc'), ('2440', '太空梭', 'electirc'), ('2456', '奇力新', 'electirc'), ('2457', '飛宏', 'electirc'), ('2460', '建通', 'electirc'), ('2462', '良得電', 'electirc'), ('2467', '志聖', 'electirc'), ('2472', '立隆電', 'electirc'), ('2476', '鉅祥', 'electirc'), ('2478', '大毅', 'electirc'), ('2483', '百容', 'electirc'), ('2484', '希華', 'electirc'), ('2492', '華新科', 'electirc'), ('2493', '揚博', 'electirc'), ('3003', '健和興', 'electirc'), ('3011', '今皓', 'electirc'), ('3015', '全漢', 'electirc'), ('3021', '鴻名', 'electirc'), ('3023', '信邦', 'electirc'), ('3026', '禾伸堂', 'electirc'), ('3032', '偉訓', 'electirc'), ('3037', '欣興', 'electirc'), ('3042', '晶技', 'electirc'), ('3044', '健鼎', 'electirc'), ('3058', '立德', 'electirc'), ('3090', '日電貿', 'electirc'), ('3092', '鴻碩', 'electirc'), ('3229', '晟鈦', 'electirc'), ('3296', '勝德', 'electirc'), ('3308', '聯德', 'electirc'), ('3321', '同泰', 'electirc'), ('3338', '泰碩', 'electirc'), ('3376', '新日興', 'electirc'), ('3432', '台端', 'electirc'), ('3501', '維熹', 'electirc'), ('3533', '嘉澤', 'electirc'), ('3550', '聯穎', 'electirc'), ('3593', '力銘', 'electirc'), ('3605', '宏致', 'electirc'), ('3607', '谷崧', 'electirc'), ('3645', '達邁', 'electirc'), ('3653', '健策', 'electirc'), ('3679', '新至陞', 'electirc'), ('4545', '銘鈺', 'electirc'), ('4912', '聯德控股-KY', 'electirc'), ('4915', '致伸', 'electirc'), ('4927', '泰鼎-KY', 'electirc'), ('4943', '康控-KY', 'electirc'), ('4958', '臻鼎-KY', 'electirc'), ('4989', '榮科', 'electirc'), ('4999', '鑫禾', 'electirc'), ('5469', '瀚宇博', 'electirc'), ('6108', '競國', 'electirc'), ('6115', '鎰勝', 'electirc'), ('6133', '金橋', 'electirc'), ('6141', '柏承', 'electirc'), ('6153', '嘉聯益', 'electirc'), ('6155', '鈞寶', 'electirc'), ('6191', '精成科', 'electirc'), ('6197', '佳必琪', 'electirc'), ('6205', '詮欣', 'electirc'), ('6213', '聯茂', 'electirc'), ('6224', '聚鼎', 'electirc'), ('6251', '定穎', 'electirc'), ('6269', '台郡', 'electirc'), ('6282', '康舒', 'electirc'), ('6412', '群電', 'electirc'), ('6449', '鈺邦', 'electirc'), ('6672', '騰輝電子-KY', 'electirc'), ('6715', '嘉基', 'electirc'), ('6781', 'AES-KY', 'electirc'), ('8039', '台虹', 'electirc'), ('8046', '南電', 'electirc'), ('8103', '瀚荃', 'electirc'), ('8213', '志超', 'electirc'), ('8249', '菱光', 'electirc'), ('2347', '聯強', 'electirc'), ('2414', '精技', 'electirc'), ('2430', '燦坤', 'electirc'), ('3010', '華立', 'electirc'), ('3028', '增你強', 'electirc'), ('3033', '威健', 'electirc'), ('3036', '文曄', 'electirc'), ('3036A', '文曄甲特', 'electirc'), ('3048', '益登', 'electirc'), ('3055', '蔚華科', 'electirc'), ('3209', '全科', 'electirc'), ('3312', '弘憶股', 'electirc'), ('3528', '安馳', 'electirc'), ('3702', '大聯大', 'electirc'), ('3702A', '大聯大甲特', 'electirc'), ('5434', '崇越', 'electirc'), ('6189', '豐藝', 'electirc'), ('6281', '全國電', 'electirc'), ('6776', '展碁國際', 'electirc'), ('8070', '長華', 'electirc'), ('8072', '陞泰', 'electirc'), ('8112', '至上', 'electirc'), ('2427', '三商電', 'electirc'), ('2453', '凌群', 'electirc'), ('2468', '華經', 'electirc'), ('2471', '資通', 'electirc'), ('2480', '敦陽科', 'electirc'), ('3029', '零壹', 'electirc'), ('3130', '一零四', 'electirc'), ('4994', '傳奇', 'electirc'), ('5203', '訊連', 'electirc'), ('6112', '聚碩', 'electirc'), ('6183', '關貿', 'electirc'), ('6214', '精誠', 'electirc'), ('2312', '金寶', 'electirc'), ('2317', '鴻海', 'electirc'), ('2354', '鴻準', 'electirc'), ('2359', '所羅門', 'electirc'), ('2360', '致茂', 'electirc'), ('2373', '震旦行', 'electirc'), ('2390', '云辰', 'electirc'), ('2404', '漢唐', 'electirc'), ('2423', '固緯', 'electirc'), ('2433', '互盛電', 'electirc'), ('2459', '敦吉', 'electirc'), ('2461', '光群雷', 'electirc'), ('2464', '盟立', 'electirc'), ('2474', '可成', 'electirc'), ('2477', '美隆電', 'electirc'), ('2482', '連宇', 'electirc'), ('2488', '漢平', 'electirc'), ('2495', '普安', 'electirc'), ('3018', '同開', 'electirc'), ('3030', '德律', 'electirc'), ('3043', '科風', 'electirc'), ('3305', '昇貿', 'electirc'), ('3518', '柏騰', 'electirc'), ('3617', '碩天', 'electirc'), ('3665', '貿聯-KY', 'electirc'), ('5225', '東科-KY', 'electirc'), ('6139', '亞翔', 'electirc'), ('6192', '巨路', 'electirc'), ('6196', '帆宣', 'electirc'), ('6201', '亞弘電', 'electirc'), ('6215', '和椿', 'electirc'), ('6283', '淳安', 'electirc'), ('6409', '旭隼', 'electirc'), ('6438', '迅得', 'electirc'), ('6558', '興能高', 'electirc'), ('6698', '旭暉應材', 'electirc'), ('6743', '安普新', 'electirc'), ('8021', '尖點', 'electirc'), ('8201', '無敵', 'electirc'), ('8499', '鼎炫-KY', 'electirc')]
stock_list_sail = [('2208', '台船', 'sail'), ('2603', '長榮', 'sail'), ('2605', '新興', 'sail'), ('2606', '裕民', 'sail'), ('2607', '榮運', 'sail'), ('2608', '嘉里大榮', 'sail'), ('2609', '陽明', 'sail'), ('2610', '華航', 'sail'), ('2611', '志信', 'sail'), ('2612', '中航', 'sail'), ('2613', '中櫃', 'sail'), ('2615', '萬海', 'sail'), ('2617', '台航', 'sail'), ('2618', '長榮航', 'sail'), ('2630', '亞航', 'sail'), ('2633', '台灣高鐵', 'sail'), ('2634', '漢翔', 'sail'), ('2636', '台驊投控', 'sail'), ('2637', '慧洋-KY', 'sail'), ('2642', '宅配通', 'sail'), ('5607', '遠雄港', 'sail'), ('5608', '四維航', 'sail'), ('8367', '建新國際', 'sail')]
stock_list_biotech = [('1598', '岱宇', 'biotech'), ('1701', '中化', 'biotech'), ('1707', '葡萄王', 'biotech'), ('1720', '生達', 'biotech'), ('1731', '美吾華', 'biotech'), ('1733', '五鼎', 'biotech'), ('1734', '杏輝', 'biotech'), ('1736', '喬山', 'biotech'), ('1760', '寶齡富錦', 'biotech'), ('1762', '中化生', 'biotech'), ('1783', '和康生', 'biotech'), ('1786', '科妍', 'biotech'), ('1789', '神隆', 'biotech'), ('1795', '美時', 'biotech'), ('3164', '景岳', 'biotech'), ('3705', '永信', 'biotech'), ('4104', '佳醫', 'biotech'), ('4106', '雃博', 'biotech'), ('4108', '懷特', 'biotech'), ('4119', '旭富', 'biotech'), ('4133', '亞諾法', 'biotech'), ('4137', '麗豐-KY', 'biotech'), ('4141', '龍燈-KY', 'biotech'), ('4142', '國光生', 'biotech'), ('4148', '全宇生技-KY', 'biotech'), ('4155', '訊映', 'biotech'), ('4164', '承業醫', 'biotech'), ('4190', '佐登-KY', 'biotech'), ('4737', '華廣', 'biotech'), ('4746', '台耀', 'biotech'), ('6491', '晶碩', 'biotech'), ('6541', '泰福-KY', 'biotech'), ('6598', 'ABC-KY', 'biotech'), ('6666', '羅麗芬-KY', 'biotech')]
stock_list_finance = [('2801', '彰銀', 'finance'), ('2809', '京城銀', 'finance'), ('2812', '台中銀', 'finance'), ('2816', '旺旺保', 'finance'), ('2820', '華票', 'finance'), ('2823', '中壽', 'finance'), ('2832', '台產', 'finance'), ('2834', '臺企銀', 'finance'), ('2836', '高雄銀', 'finance'), ('2836A', '高雄銀甲特', 'finance'), ('2838', '聯邦銀', 'finance'), ('2838A', '聯邦銀甲特', 'finance'), ('2845', '遠東銀', 'finance'), ('2849', '安泰銀', 'finance'), ('2850', '新產', 'finance'), ('2851', '中再保', 'finance'), ('2852', '第一保', 'finance'), ('2855', '統一證', 'finance'), ('2867', '三商壽', 'finance'), ('2880', '華南金', 'finance'), ('2881', '富邦金', 'finance'), ('2881A', '富邦特', 'finance'), ('2881B', '富邦金乙特', 'finance'), ('2882', '國泰金', 'finance'), ('2882A', '國泰特', 'finance'), ('2882B', '國泰金乙特', 'finance'), ('2883', '開發金', 'finance'), ('2884', '玉山金', 'finance'), ('2885', '元大金', 'finance'), ('2886', '兆豐金', 'finance'), ('2887', '台新金', 'finance'), ('2887E', '台新戊特', 'finance'), ('2887F', '台新戊特二', 'finance'), ('2888', '新光金', 'finance'), ('2888A', '新光金甲特', 'finance'), ('2888B', '新光金乙特', 'finance'), ('2889', '國票金', 'finance'), ('2890', '永豐金', 'finance'), ('2891', '中信金', 'finance'), ('2891B', '中信金乙特', 'finance'), ('2891C', '中信金丙特', 'finance'), ('2892', '第一金', 'finance'), ('2897', '王道銀行', 'finance'), ('2897A', '王道銀甲特', 'finance'), ('5876', '上海商銀', 'finance'), ('5880', '合庫金', 'finance'), ('6005', '群益證', 'finance'), ('6024', '群益期', 'finance')]
stock_list_tsmc = [('2330', '台積電', 'tsmc')]

stock_list_electric_car = [list(k) for k in stock_list_electric_car]
stock_list_electric = [list(k) for k in stock_list_electric]
stock_list_sail = [list(k) for k in stock_list_sail]
stock_list_biotech = [list(k) for k in stock_list_biotech]
stock_list_finance = [list(k) for k in stock_list_finance]
stock_list_tsmc = [list(k) for k in stock_list_tsmc]
print(stock_list_electric_car)
print(stock_list_electric)
print(stock_list_sail)
print(stock_list_biotech)
print(stock_list_finance)
print(stock_list_tsmc)



