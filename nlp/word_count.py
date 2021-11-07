#coding=utf-8
import jieba
import model_mysql
import model_mongo
import json
from pprint import pprint
from datetime import datetime
import pandas as pd
from collections import Counter, defaultdict
import time

# SOURCE = 'ptt'
SOURCE = 'cnyes'

print(SOURCE)

# 類股列表
stock_list_total = [('4746', '台耀', 'biotech'), ('6491', '晶碩', 'biotech'), ('6541', '泰福-KY', 'biotech'), ('6598', 'ABC-KY', 'biotech'), ('6666', '羅麗芬-KY', 'biotech'), ('1598', '岱宇', 'biotech'), ('1701', '中化', 'biotech'), ('1707', '葡萄王', 'biotech'), ('1720', '生達', 'biotech'), ('1731', '美吾華', 'biotech'), ('1733', '五鼎', 'biotech'), ('1734', '杏輝', 'biotech'), ('1736', '喬山', 'biotech'), ('1760', '寶齡富錦', 'biotech'), ('1762', '中化生', 'biotech'), ('1783', '和康生', 'biotech'), ('1786', '科妍', 'biotech'), ('1789', '神隆', 'biotech'), ('1795', '美時', 'biotech'), ('3164', '景岳', 'biotech'), ('3705', '永信', 'biotech'), ('4104', '佳醫', 'biotech'), ('4106', '雃博', 'biotech'), ('4108', '懷特', 'biotech'), ('4119', '旭富', 'biotech'), ('4133', '亞諾法', 'biotech'), ('4137', '麗豐-KY', 'biotech'), ('4141', '龍燈-KY', 'biotech'), ('4142', '國光生', 'biotech'), ('4148', '全宇生技-KY', 'biotech'), ('4155', '訊映', 'biotech'), ('4164', '承業醫', 'biotech'), ('4190', '佐登-KY', 'biotech'), ('4737', '華廣', 'biotech'), ('1471', '首利', 'electric'), ('1582', '信錦', 'electric'), ('2059', '川湖', 'electric'), ('2305', '全友', 'electric'), ('2312', '金寶', 'electric'), ('2313', '華通', 'electric'), ('2314', '台揚', 'electric'), ('2316', '楠梓電', 'electric'), ('2321', '東訊', 'electric'), ('2323', '中環', 'electric'), ('2324', '仁寶', 'electric'), ('2327', '國巨', 'electric'), ('2328', '廣宇', 'electric'), ('2331', '精英', 'electric'), ('2332', '友訊', 'electric'), ('2340', '光磊', 'electric'), ('2345', '智邦', 'electric'), ('2347', '聯強', 'electric'), ('2349', '錸德', 'electric'), ('2352', '佳世達', 'electric'), ('2353', '宏碁', 'electric'), ('2354', '鴻準', 'electric'), ('2355', '敬鵬', 'electric'), ('2356', '英業達', 'electric'), ('2359', '所羅門', 'electric'), ('2360', '致茂', 'electric'), ('2362', '藍天', 'electric'), ('2364', '倫飛', 'electric'), ('2365', '昆盈', 'electric'), ('2367', '燿華', 'electric'), ('2368', '金像電', 'electric'), ('2373', '震旦行', 'electric'), ('2374', '佳能', 'electric'), ('2375', '凱美', 'electric'), ('2376', '技嘉', 'electric'), ('2377', '微星', 'electric'), ('2380', '虹光', 'electric'), ('2382', '廣達', 'electric'), ('2383', '台光電', 'electric'), ('2385', '群光', 'electric'), ('2387', '精元', 'electric'), ('2390', '云辰', 'electric'), ('2393', '億光', 'electric'), ('2395', '研華', 'electric'), ('2397', '友通', 'electric'), ('2399', '映泰', 'electric'), ('2402', '毅嘉', 'electric'), ('2404', '漢唐', 'electric'), ('2405', '浩鑫', 'electric'), ('2406', '國碩', 'electric'), ('2409', '友達', 'electric'), ('2412', '中華電', 'electric'), ('2413', '環科', 'electric'), ('2414', '精技', 'electric'), ('2415', '錩新', 'electric'), ('2417', '圓剛', 'electric'), ('2419', '仲琦', 'electric'), ('2420', '新巨', 'electric'), ('2423', '固緯', 'electric'), ('2424', '隴華', 'electric'), ('2425', '承啟', 'electric'), ('2426', '鼎元', 'electric'), ('2427', '三商電', 'electric'), ('2428', '興勤', 'electric'), ('2429', '銘旺科', 'electric'), ('2430', '燦坤', 'electric'), ('2431', '聯昌', 'electric'), ('2433', '互盛電', 'electric'), ('2438', '翔耀', 'electric'), ('2439', '美律', 'electric'), ('2440', '太空梭', 'electric'), ('2442', '新美齊', 'electric'), ('2444', '兆勁', 'electric'), ('2450', '神腦', 'electric'), ('2453', '凌群', 'electric'), ('2455', '全新', 'electric'), ('2456', '奇力新', 'electric'), ('2457', '飛宏', 'electric'), ('2460', '建通', 'electric'), ('2461', '光群雷', 'electric'), ('2462', '良得電', 'electric'), ('2464', '盟立', 'electric'), ('2465', '麗臺', 'electric'), ('2466', '冠西電', 'electric'), ('2467', '志聖', 'electric'), ('2468', '華經', 'electric'), ('2471', '資通', 'electric'), ('2472', '立隆電', 'electric'), ('2474', '可成', 'electric'), ('2476', '鉅祥', 'electric'), ('2477', '美隆電', 'electric'), ('2478', '大毅', 'electric'), ('2480', '敦陽科', 'electric'), ('2482', '連宇', 'electric'), ('2484', '希華', 'electric'), ('2485', '兆赫', 'electric'), ('2486', '一詮', 'electric'), ('2488', '漢平', 'electric'), ('2489', '瑞軒', 'electric'), ('2491', '吉祥全', 'electric'), ('2492', '華新科', 'electric'), ('2493', '揚博', 'electric'), ('2495', '普安', 'electric'), ('2498', '宏達電', 'electric'), ('3002', '歐格', 'electric'), ('3003', '健和興', 'electric'), ('3005', '神基', 'electric'), ('3008', '大立光', 'electric'), ('3010', '華立', 'electric'), ('3011', '今皓', 'electric'), ('3013', '晟銘電', 'electric'), ('3015', '全漢', 'electric'), ('3017', '奇鋐', 'electric'), ('3018', '同開', 'electric'), ('3019', '亞光', 'electric'), ('3021', '鴻名', 'electric'), ('3022', '威強電', 'electric'), ('3024', '憶聲', 'electric'), ('3025', '星通', 'electric'), ('3026', '禾伸堂', 'electric'), ('3027', '盛達', 'electric'), ('3028', '增你強', 'electric'), ('3029', '零壹', 'electric'), ('3030', '德律', 'electric'), ('3031', '佰鴻', 'electric'), ('3032', '偉訓', 'electric'), ('3033', '威健', 'electric'), ('3036', '文曄', 'electric'), ('3036A', '文曄甲特', 'electric'), ('3037', '欣興', 'electric'), ('3038', '全台', 'electric'), ('3042', '晶技', 'electric'), ('3043', '科風', 'electric'), ('3044', '健鼎', 'electric'), ('3045', '台灣大', 'electric'), ('3046', '啟碁', 'electric'), ('3047', '訊舟', 'electric'), ('3048', '益登', 'electric'), ('3049', '和鑫', 'electric'), ('3050', '鈺德', 'electric'), ('3051', '力特', 'electric'), ('3055', '蔚華科', 'electric'), ('3057', '喬鼎', 'electric'), ('3058', '立德', 'electric'), ('3059', '華晶科', 'electric'), ('3060', '銘異', 'electric'), ('3062', '建漢', 'electric'), ('3090', '日電貿', 'electric'), ('3092', '鴻碩', 'electric'), ('3130', '一零四', 'electric'), ('3138', '耀登', 'electric'), ('3149', '正達', 'electric'), ('3209', '全科', 'electric'), ('3229', '晟鈦', 'electric'), ('3231', '緯創', 'electric'), ('3296', '勝德', 'electric'), ('3305', '昇貿', 'electric'), ('3308', '聯德', 'electric'), ('3311', '閎暉', 'electric'), ('3312', '弘憶股', 'electric'), ('3321', '同泰', 'electric'), ('3338', '泰碩', 'electric'), ('3356', '奇偶', 'electric'), ('3376', '新日興', 'electric'), ('3380', '明泰', 'electric'), ('3383', '新世紀', 'electric'), ('3406', '玉晶光', 'electric'), ('3416', '融程電', 'electric'), ('3419', '譁裕', 'electric'), ('3432', '台端', 'electric'), ('3437', '榮創', 'electric'), ('3454', '晶睿', 'electric'), ('3481', '群創', 'electric'), ('3494', '誠研', 'electric'), ('3501', '維熹', 'electric'), ('3504', '揚明光', 'electric'), ('3515', '華擎', 'electric'), ('3518', '柏騰', 'electric'), ('3528', '安馳', 'electric'), ('3533', '嘉澤', 'electric'), ('3535', '晶彩科', 'electric'), ('3543', '州巧', 'electric'), ('3550', '聯穎', 'electric'), ('3563', '牧德', 'electric'), ('3576', '聯合再生', 'electric'), ('3591', '艾笛森', 'electric'), ('3593', '力銘', 'electric'), ('3596', '智易', 'electric'), ('3605', '宏致', 'electric'), ('3607', '谷崧', 'electric'), ('3617', '碩天', 'electric'), ('3622', '洋華', 'electric'), ('3645', '達邁', 'electric'), ('3653', '健策', 'electric'), ('3669', '圓展', 'electric'), ('3673', 'TPK-KY', 'electric'), ('3679', '新至陞', 'electric'), ('3682', '亞太電', 'electric'), ('3694', '海華', 'electric'), ('3701', '大眾控', 'electric'), ('3702', '大聯大', 'electric'), ('3702A', '大聯大甲特', 'electric'), ('3704', '合勤控', 'electric'), ('3706', '神達', 'electric'), ('3712', '永崴投控', 'electric'), ('3714', '富采', 'electric'), ('4545', '銘鈺', 'electric'), ('4904', '遠傳', 'electric'), ('4906', '正文', 'electric'), ('4912', '聯德控股-KY', 'electric'), ('4915', '致伸', 'electric'), ('4916', '事欣科', 'electric'), ('4927', '泰鼎-KY', 'electric'), ('4934', '太極', 'electric'), ('4935', '茂林-KY', 'electric'), ('4938', '和碩', 'electric'), ('4942', '嘉彰', 'electric'), ('4943', '康控-KY', 'electric'), ('4956', '光鋐', 'electric'), ('4958', '臻鼎-KY', 'electric'), ('4960', '誠美材', 'electric'), ('4976', '佳凌', 'electric'), ('4977', '眾達-KY', 'electric'), ('4989', '榮科', 'electric'), ('4994', '傳奇', 'electric'), ('5203', '訊連', 'electric'), ('5215', '科嘉-KY', 'electric'), ('5225', '東科-KY', 'electric'), ('5234', '達興材料', 'electric'), ('5243', '乙盛-KY', 'electric'), ('5258', '虹堡', 'electric'), ('5388', '中磊', 'electric'), ('5434', '崇越', 'electric'), ('5469', '瀚宇博', 'electric'), ('5484', '慧友', 'electric'), ('6108', '競國', 'electric'), ('6112', '聚碩', 'electric'), ('6115', '鎰勝', 'electric'), ('6116', '彩晶', 'electric'), ('6117', '迎廣', 'electric'), ('6120', '達運', 'electric'), ('6128', '上福', 'electric'), ('6133', '金橋', 'electric'), ('6136', '富爾特', 'electric'), ('6139', '亞翔', 'electric'), ('6141', '柏承', 'electric'), ('6142', '友勁', 'electric'), ('6152', '百一', 'electric'), ('6153', '嘉聯益', 'electric'), ('6155', '鈞寶', 'electric'), ('6164', '華興', 'electric'), ('6166', '凌華', 'electric'), ('6168', '宏齊', 'electric'), ('6172', '互億', 'electric'), ('6176', '瑞儀', 'electric'), ('6183', '關貿', 'electric'), ('6189', '豐藝', 'electric'), ('6191', '精成科', 'electric'), ('6192', '巨路', 'electric'), ('6196', '帆宣', 'electric'), ('6197', '佳必琪', 'electric'), ('6201', '亞弘電', 'electric'), ('6205', '詮欣', 'electric'), ('6206', '飛捷', 'electric'), ('6209', '今國光', 'electric'), ('6213', '聯茂', 'electric'), ('6214', '精誠', 'electric'), ('6215', '和椿', 'electric'), ('6216', '居易', 'electric'), ('6224', '聚鼎', 'electric'), ('6225', '天瀚', 'electric'), ('6226', '光鼎', 'electric'), ('6230', '尼得科超眾', 'electric'), ('6235', '華孚', 'electric'), ('6251', '定穎', 'electric'), ('6269', '台郡', 'electric'), ('6277', '宏正', 'electric'), ('6278', '台表科', 'electric'), ('6281', '全國電', 'electric'), ('6283', '淳安', 'electric'), ('6285', '啟碁', 'electric'), ('6289', '華上', 'electric'), ('6405', '悅城', 'electric'), ('6409', '旭隼', 'electric'), ('6412', '群電', 'electric'), ('6414', '樺漢', 'electric'), ('6416', '瑞祺電通', 'electric'), ('6426', '統新', 'electric'), ('6431', '光麗-KY', 'electric'), ('6438', '迅得', 'electric'), ('6442', '光聖', 'electric'), ('6449', '鈺邦', 'electric'), ('6456', 'GIS-KY', 'electric'), ('6477', '安集', 'electric'), ('6558', '興能高', 'electric'), ('6579', '研揚', 'electric'), ('6591', '動力-KY', 'electric'), ('6668', '中揚光', 'electric'), ('6669', '緯穎', 'electric'), ('6672', '騰輝電子-KY', 'electric'), ('6674', '鋐寶科技', 'electric'), ('6698', '旭暉應材', 'electric'), ('6706', '惠特', 'electric'), ('6715', '嘉基', 'electric'), ('6743', '安普新', 'electric'), ('6776', '展碁國際', 'electric'), ('6781', 'AES-KY', 'electric'), ('8011', '台通', 'electric'), ('8021', '尖點', 'electric'), ('8039', '台虹', 'electric'), ('8046', '南電', 'electric'), ('8070', '長華', 'electric'), ('8072', '陞泰', 'electric'), ('8101', '華冠', 'electric'), ('8103', '瀚荃', 'electric'), ('8104', '錸寶', 'electric'), ('8105', '凌巨', 'electric'), ('8112', '至上', 'electric'), ('8114', '振樺電', 'electric'), ('8163', '達方', 'electric'), ('8201', '無敵', 'electric'), ('8210', '勤誠', 'electric'), ('8213', '志超', 'electric'), ('8215', '明基材', 'electric'), ('8249', '菱光', 'electric'), ('8499', '鼎炫-KY', 'electric'), ('9912', '偉聯', 'electric'), ('4999', '鑫禾', 'electric, electric_car'), ('6282', '康舒', 'electric, electric_car'), ('6443', '元晶', 'electric, electric_car'), ('2301', '光寶科', 'electric, electric_car'), ('2308', '台達電', 'electric, electric_car'), ('2317', '鴻海', 'electric, electric_car'), ('2357', '華碩', 'electric, electric_car'), ('2392', '正崴', 'electric, electric_car'), ('2421', '建準', 'electric, electric_car'), ('2459', '敦吉', 'electric, electric_car'), ('2483', '百容', 'electric, electric_car'), ('3023', '信邦', 'electric, electric_car'), ('3665', '貿聯-KY', 'electric, electric_car'), ('1503', '士電', 'electric_car'), ('1519', '華城', 'electric_car'), ('1533', '車王電', 'electric_car'), ('1536', '和大', 'electric_car'), ('1537', '廣隆', 'electric_car'), ('1587', '吉茂', 'electric_car'), ('1599', '宏佳騰', 'electric_car'), ('1611', '中電', 'electric_car'), ('1723', '中碳', 'electric_car'), ('2237', '華德動能', 'electric_car'), ('2371', '大同', 'electric_car'), ('4503', '金雨', 'electric_car'), ('4721', '美琪瑪', 'electric_car'), ('4738', '尚化', 'electric_car'), ('4739', '康普', 'electric_car'), ('5227', '立凱-KY', 'electric_car'), ('5233', '有量', 'electric_car'), ('5439', '高技', 'electric_car'), ('6121', '新普', 'electric_car'), ('6275', '元山', 'electric_car'), ('8038', '長園科', 'electric_car'), ('8109', '博大', 'electric_car'), ('8171', '天宇', 'electric_car'), ('8183', '精星', 'electric_car'), ('8358', '金居', 'electric_car'), ('8933', '愛地雅', 'electric_car'), ('8937', '合騏', 'electric_car'), ('9914', '美利達', 'electric_car'), ('5876', '上海商銀', 'finance'), ('5880', '合庫金', 'finance'), ('6005', '群益證', 'finance'), ('6024', '群益期', 'finance'), ('2801', '彰銀', 'finance'), ('2809', '京城銀', 'finance'), ('2812', '台中銀', 'finance'), ('2816', '旺旺保', 'finance'), ('2820', '華票', 'finance'), ('2823', '中壽', 'finance'), ('2832', '台產', 'finance'), ('2834', '臺企銀', 'finance'), ('2836', '高雄銀', 'finance'), ('2836A', '高雄銀甲特', 'finance'), ('2838', '聯邦銀', 'finance'), ('2838A', '聯邦銀甲特', 'finance'), ('2845', '遠東銀', 'finance'), ('2849', '安泰銀', 'finance'), ('2850', '新產', 'finance'), ('2851', '中再保', 'finance'), ('2852', '第一保', 'finance'), ('2855', '統一證', 'finance'), ('2867', '三商壽', 'finance'), ('2880', '華南金', 'finance'), ('2881', '富邦金', 'finance'), ('2881A', '富邦特', 'finance'), ('2881B', '富邦金乙特', 'finance'), ('2882', '國泰金', 'finance'), ('2882A', '國泰特', 'finance'), ('2882B', '國泰金乙特', 'finance'), ('2883', '開發金', 'finance'), ('2884', '玉山金', 'finance'), ('2885', '元大金', 'finance'), ('2886', '兆豐金', 'finance'), ('2887', '台新金', 'finance'), ('2887E', '台新戊特', 'finance'), ('2887F', '台新戊特二', 'finance'), ('2888', '新光金', 'finance'), ('2888A', '新光金甲特', 'finance'), ('2888B', '新光金乙特', 'finance'), ('2889', '國票金', 'finance'), ('2890', '永豐金', 'finance'), ('2891', '中信金', 'finance'), ('2891B', '中信金乙特', 'finance'), ('2891C', '中信金丙特', 'finance'), ('2892', '第一金', 'finance'), ('2897', '王道銀行', 'finance'), ('2897A', '王道銀甲特', 'finance'), ('2208', '台船', 'sail'), ('2603', '長榮', 'sail'), ('2605', '新興', 'sail'), ('2606', '裕民', 'sail'), ('2607', '榮運', 'sail'), ('2608', '嘉里大榮', 'sail'), ('2609', '陽明', 'sail'), ('2610', '華航', 'sail'), ('2611', '志信', 'sail'), ('2612', '中航', 'sail'), ('2613', '中櫃', 'sail'), ('2615', '萬海', 'sail'), ('2617', '台航', 'sail'), ('2618', '長榮航', 'sail'), ('2630', '亞航', 'sail'), ('2633', '台灣高鐵', 'sail'), ('2634', '漢翔', 'sail'), ('2636', '台驊投控', 'sail'), ('2637', '慧洋-KY', 'sail'), ('2642', '宅配通', 'sail'), ('5607', '遠雄港', 'sail'), ('5608', '四維航', 'sail'), ('8367', '建新國際', 'sail'), ('2330', '台積電', 'stock_market')]

# 1
stock_list_electric_car = [('1503', '士電', 'electric_car'), ('1519', '華城', 'electric_car'), ('1533', '車王電', 'electric_car'), ('1536', '和大', 'electric_car'), ('1537', '廣隆', 'electric_car'), ('1587', '吉茂', 'electric_car'), ('1599', '宏佳騰', 'electric_car'), ('1611', '中電', 'electric_car'), ('1723', '中碳', 'electric_car'), ('2237', '華德動能', 'electric_car'), ('2301', '光寶科', 'electric, electric_car'), ('2308', '台達電', 'electric, electric_car'), ('2317', '鴻海', 'electric, electric_car'), ('2357', '華碩', 'electric, electric_car'), ('2371', '大同', 'electric_car'), ('2392', '正崴', 'electric, electric_car'), ('2421', '建準', 'electric, electric_car'), ('2459', '敦吉', 'electric, electric_car'), ('2483', '百容', 'electric, electric_car'), ('3023', '信邦', 'electric, electric_car'), ('3665', '貿聯-KY', 'electric, electric_car'), ('4503', '金雨', 'electric_car'), ('4721', '美琪瑪', 'electric_car'), ('4738', '尚化', 'electric_car'), ('4739', '康普', 'electric_car'), ('4999', '鑫禾', 'electric, electric_car'), ('5227', '立凱-KY', 'electric_car'), ('5233', '有量', 'electric_car'), ('5439', '高技', 'electric_car'), ('6121', '新普', 'electric_car'), ('6275', '元山', 'electric_car'), ('6282', '康舒', 'electric, electric_car'), ('6443', '元晶', 'electric, electric_car'), ('8038', '長園科', 'electric_car'), ('8109', '博大', 'electric_car'), ('8171', '天宇', 'electric_car'), ('8183', '精星', 'electric_car'), ('8358', '金居', 'electric_car'), ('8933', '愛地雅', 'electric_car'), ('8937', '合騏', 'electric_car'), ('9914', '美利達', 'electric_car')]
# 2
stock_list_electric = [('1471', '首利', 'electric'), ('1582', '信錦', 'electric'), ('2059', '川湖', 'electric'), ('2305', '全友', 'electric'), ('2312', '金寶', 'electric'), ('2313', '華通', 'electric'), ('2314', '台揚', 'electric'), ('2316', '楠梓電', 'electric'), ('2321', '東訊', 'electric'), ('2323', '中環', 'electric'), ('2324', '仁寶', 'electric'), ('2327', '國巨', 'electric'), ('2328', '廣宇', 'electric'), ('2331', '精英', 'electric'), ('2332', '友訊', 'electric'), ('2340', '光磊', 'electric'), ('2345', '智邦', 'electric'), ('2347', '聯強', 'electric'), ('2349', '錸德', 'electric'), ('2352', '佳世達', 'electric'), ('2353', '宏碁', 'electric'), ('2354', '鴻準', 'electric'), ('2355', '敬鵬', 'electric'), ('2356', '英業達', 'electric'), ('2359', '所羅門', 'electric'), ('2360', '致茂', 'electric'), ('2362', '藍天', 'electric'), ('2364', '倫飛', 'electric'), ('2365', '昆盈', 'electric'), ('2367', '燿華', 'electric'), ('2368', '金像電', 'electric'), ('2373', '震旦行', 'electric'), ('2374', '佳能', 'electric'), ('2375', '凱美', 'electric'), ('2376', '技嘉', 'electric'), ('2377', '微星', 'electric'), ('2380', '虹光', 'electric'), ('2382', '廣達', 'electric'), ('2383', '台光電', 'electric'), ('2385', '群光', 'electric'), ('2387', '精元', 'electric'), ('2390', '云辰', 'electric'), ('2393', '億光', 'electric'), ('2395', '研華', 'electric'), ('2397', '友通', 'electric'), ('2399', '映泰', 'electric'), ('2402', '毅嘉', 'electric'), ('2404', '漢唐', 'electric'), ('2405', '浩鑫', 'electric'), ('2406', '國碩', 'electric'), ('2409', '友達', 'electric'), ('2412', '中華電', 'electric'), ('2413', '環科', 'electric'), ('2414', '精技', 'electric'), ('2415', '錩新', 'electric'), ('2417', '圓剛', 'electric'), ('2419', '仲琦', 'electric'), ('2420', '新巨', 'electric'), ('2423', '固緯', 'electric'), ('2424', '隴華', 'electric'), ('2425', '承啟', 'electric'), ('2426', '鼎元', 'electric'), ('2427', '三商電', 'electric'), ('2428', '興勤', 'electric'), ('2429', '銘旺科', 'electric'), ('2430', '燦坤', 'electric'), ('2431', '聯昌', 'electric'), ('2433', '互盛電', 'electric'), ('2438', '翔耀', 'electric'), ('2439', '美律', 'electric'), ('2440', '太空梭', 'electric'), ('2442', '新美齊', 'electric'), ('2444', '兆勁', 'electric'), ('2450', '神腦', 'electric'), ('2453', '凌群', 'electric'), ('2455', '全新', 'electric'), ('2456', '奇力新', 'electric'), ('2457', '飛宏', 'electric'), ('2460', '建通', 'electric'), ('2461', '光群雷', 'electric'), ('2462', '良得電', 'electric'), ('2464', '盟立', 'electric'), ('2465', '麗臺', 'electric'), ('2466', '冠西電', 'electric'), ('2467', '志聖', 'electric'), ('2468', '華經', 'electric'), ('2471', '資通', 'electric'), ('2472', '立隆電', 'electric'), ('2474', '可成', 'electric'), ('2476', '鉅祥', 'electric'), ('2477', '美隆電', 'electric'), ('2478', '大毅', 'electric'), ('2480', '敦陽科', 'electric'), ('2482', '連宇', 'electric'), ('2484', '希華', 'electric'), ('2485', '兆赫', 'electric'), ('2486', '一詮', 'electric'), ('2488', '漢平', 'electric'), ('2489', '瑞軒', 'electric'), ('2491', '吉祥全', 'electric'), ('2492', '華新科', 'electric'), ('2493', '揚博', 'electric'), ('2495', '普安', 'electric'), ('2498', '宏達電', 'electric'), ('3002', '歐格', 'electric'), ('3003', '健和興', 'electric'), ('3005', '神基', 'electric'), ('3008', '大立光', 'electric'), ('3010', '華立', 'electric'), ('3011', '今皓', 'electric'), ('3013', '晟銘電', 'electric'), ('3015', '全漢', 'electric'), ('3017', '奇鋐', 'electric'), ('3018', '同開', 'electric'), ('3019', '亞光', 'electric'), ('3021', '鴻名', 'electric'), ('3022', '威強電', 'electric'), ('3024', '憶聲', 'electric'), ('3025', '星通', 'electric'), ('3026', '禾伸堂', 'electric'), ('3027', '盛達', 'electric'), ('3028', '增你強', 'electric'), ('3029', '零壹', 'electric'), ('3030', '德律', 'electric'), ('3031', '佰鴻', 'electric'), ('3032', '偉訓', 'electric'), ('3033', '威健', 'electric'), ('3036', '文曄', 'electric'), ('3036A', '文曄甲特', 'electric'), ('3037', '欣興', 'electric'), ('3038', '全台', 'electric'), ('3042', '晶技', 'electric'), ('3043', '科風', 'electric'), ('3044', '健鼎', 'electric'), ('3045', '台灣大', 'electric'), ('3046', '啟碁', 'electric'), ('3047', '訊舟', 'electric'), ('3048', '益登', 'electric'), ('3049', '和鑫', 'electric'), ('3050', '鈺德', 'electric'), ('3051', '力特', 'electric'), ('3055', '蔚華科', 'electric'), ('3057', '喬鼎', 'electric'), ('3058', '立德', 'electric'), ('3059', '華晶科', 'electric'), ('3060', '銘異', 'electric'), ('3062', '建漢', 'electric'), ('3090', '日電貿', 'electric'), ('3092', '鴻碩', 'electric'), ('3130', '一零四', 'electric'), ('3138', '耀登', 'electric'), ('3149', '正達', 'electric'), ('3209', '全科', 'electric'), ('3229', '晟鈦', 'electric'), ('3231', '緯創', 'electric'), ('3296', '勝德', 'electric'), ('3305', '昇貿', 'electric'), ('3308', '聯德', 'electric'), ('3311', '閎暉', 'electric'), ('3312', '弘憶股', 'electric'), ('3321', '同泰', 'electric'), ('3338', '泰碩', 'electric'), ('3356', '奇偶', 'electric'), ('3376', '新日興', 'electric'), ('3380', '明泰', 'electric'), ('3383', '新世紀', 'electric'), ('3406', '玉晶光', 'electric'), ('3416', '融程電', 'electric'), ('3419', '譁裕', 'electric'), ('3432', '台端', 'electric'), ('3437', '榮創', 'electric'), ('3454', '晶睿', 'electric'), ('3481', '群創', 'electric'), ('3494', '誠研', 'electric'), ('3501', '維熹', 'electric'), ('3504', '揚明光', 'electric'), ('3515', '華擎', 'electric'), ('3518', '柏騰', 'electric'), ('3528', '安馳', 'electric'), ('3533', '嘉澤', 'electric'), ('3535', '晶彩科', 'electric'), ('3543', '州巧', 'electric'), ('3550', '聯穎', 'electric'), ('3563', '牧德', 'electric'), ('3576', '聯合再生', 'electric'), ('3591', '艾笛森', 'electric'), ('3593', '力銘', 'electric'), ('3596', '智易', 'electric'), ('3605', '宏致', 'electric'), ('3607', '谷崧', 'electric'), ('3617', '碩天', 'electric'), ('3622', '洋華', 'electric'), ('3645', '達邁', 'electric'), ('3653', '健策', 'electric'), ('3669', '圓展', 'electric'), ('3673', 'TPK-KY', 'electric'), ('3679', '新至陞', 'electric'), ('3682', '亞太電', 'electric'), ('3694', '海華', 'electric'), ('3701', '大眾控', 'electric'), ('3702', '大聯大', 'electric'), ('3702A', '大聯大甲特', 'electric'), ('3704', '合勤控', 'electric'), ('3706', '神達', 'electric'), ('3712', '永崴投控', 'electric'), ('3714', '富采', 'electric'), ('4545', '銘鈺', 'electric'), ('4904', '遠傳', 'electric'), ('4906', '正文', 'electric'), ('4912', '聯德控股-KY', 'electric'), ('4915', '致伸', 'electric'), ('4916', '事欣科', 'electric'), ('4927', '泰鼎-KY', 'electric'), ('4934', '太極', 'electric'), ('4935', '茂林-KY', 'electric'), ('4938', '和碩', 'electric'), ('4942', '嘉彰', 'electric'), ('4943', '康控-KY', 'electric'), ('4956', '光鋐', 'electric'), ('4958', '臻鼎-KY', 'electric'), ('4960', '誠美材', 'electric'), ('4976', '佳凌', 'electric'), ('4977', '眾達-KY', 'electric'), ('4989', '榮科', 'electric'), ('4994', '傳奇', 'electric'), ('5203', '訊連', 'electric'), ('5215', '科嘉-KY', 'electric'), ('5225', '東科-KY', 'electric'), ('5234', '達興材料', 'electric'), ('5243', '乙盛-KY', 'electric'), ('5258', '虹堡', 'electric'), ('5388', '中磊', 'electric'), ('5434', '崇越', 'electric'), ('5469', '瀚宇博', 'electric'), ('5484', '慧友', 'electric'), ('6108', '競國', 'electric'), ('6112', '聚碩', 'electric'), ('6115', '鎰勝', 'electric'), ('6116', '彩晶', 'electric'), ('6117', '迎廣', 'electric'), ('6120', '達運', 'electric'), ('6128', '上福', 'electric'), ('6133', '金橋', 'electric'), ('6136', '富爾特', 'electric'), ('6139', '亞翔', 'electric'), ('6141', '柏承', 'electric'), ('6142', '友勁', 'electric'), ('6152', '百一', 'electric'), ('6153', '嘉聯益', 'electric'), ('6155', '鈞寶', 'electric'), ('6164', '華興', 'electric'), ('6166', '凌華', 'electric'), ('6168', '宏齊', 'electric'), ('6172', '互億', 'electric'), ('6176', '瑞儀', 'electric'), ('6183', '關貿', 'electric'), ('6189', '豐藝', 'electric'), ('6191', '精成科', 'electric'), ('6192', '巨路', 'electric'), ('6196', '帆宣', 'electric'), ('6197', '佳必琪', 'electric'), ('6201', '亞弘電', 'electric'), ('6205', '詮欣', 'electric'), ('6206', '飛捷', 'electric'), ('6209', '今國光', 'electric'), ('6213', '聯茂', 'electric'), ('6214', '精誠', 'electric'), ('6215', '和椿', 'electric'), ('6216', '居易', 'electric'), ('6224', '聚鼎', 'electric'), ('6225', '天瀚', 'electric'), ('6226', '光鼎', 'electric'), ('6230', '尼得科超眾', 'electric'), ('6235', '華孚', 'electric'), ('6251', '定穎', 'electric'), ('6269', '台郡', 'electric'), ('6277', '宏正', 'electric'), ('6278', '台表科', 'electric'), ('6281', '全國電', 'electric'), ('6283', '淳安', 'electric'), ('6285', '啟碁', 'electric'), ('6289', '華上', 'electric'), ('6405', '悅城', 'electric'), ('6409', '旭隼', 'electric'), ('6412', '群電', 'electric'), ('6414', '樺漢', 'electric'), ('6416', '瑞祺電通', 'electric'), ('6426', '統新', 'electric'), ('6431', '光麗-KY', 'electric'), ('6438', '迅得', 'electric'), ('6442', '光聖', 'electric'), ('6449', '鈺邦', 'electric'), ('6456', 'GIS-KY', 'electric'), ('6477', '安集', 'electric'), ('6558', '興能高', 'electric'), ('6579', '研揚', 'electric'), ('6591', '動力-KY', 'electric'), ('6668', '中揚光', 'electric'), ('6669', '緯穎', 'electric'), ('6672', '騰輝電子-KY', 'electric'), ('6674', '鋐寶科技', 'electric'), ('6698', '旭暉應材', 'electric'), ('6706', '惠特', 'electric'), ('6715', '嘉基', 'electric'), ('6743', '安普新', 'electric'), ('6776', '展碁國際', 'electric'), ('6781', 'AES-KY', 'electric'), ('8011', '台通', 'electric'), ('8021', '尖點', 'electric'), ('8039', '台虹', 'electric'), ('8046', '南電', 'electric'), ('8070', '長華', 'electric'), ('8072', '陞泰', 'electric'), ('8101', '華冠', 'electric'), ('8103', '瀚荃', 'electric'), ('8104', '錸寶', 'electric'), ('8105', '凌巨', 'electric'), ('8112', '至上', 'electric'), ('8114', '振樺電', 'electric'), ('8163', '達方', 'electric'), ('8201', '無敵', 'electric'), ('8210', '勤誠', 'electric'), ('8213', '志超', 'electric'), ('8215', '明基材', 'electric'), ('8249', '菱光', 'electric'), ('8499', '鼎炫-KY', 'electric'), ('9912', '偉聯', 'electric')]
# 3
stock_list_sail = [('2208', '台船', 'sail'), ('2603', '長榮', 'sail'), ('2605', '新興', 'sail'), ('2606', '裕民', 'sail'), ('2607', '榮運', 'sail'), ('2608', '嘉里大榮', 'sail'), ('2609', '陽明', 'sail'), ('2610', '華航', 'sail'), ('2611', '志信', 'sail'), ('2612', '中航', 'sail'), ('2613', '中櫃', 'sail'), ('2615', '萬海', 'sail'), ('2617', '台航', 'sail'), ('2618', '長榮航', 'sail'), ('2630', '亞航', 'sail'), ('2633', '台灣高鐵', 'sail'), ('2634', '漢翔', 'sail'), ('2636', '台驊投控', 'sail'), ('2637', '慧洋-KY', 'sail'), ('2642', '宅配通', 'sail'), ('5607', '遠雄港', 'sail'), ('5608', '四維航', 'sail'), ('8367', '建新國際', 'sail')]
# 4
stock_list_biotech = [('1598', '岱宇', 'biotech'), ('1701', '中化', 'biotech'), ('1707', '葡萄王', 'biotech'), ('1720', '生達', 'biotech'), ('1731', '美吾華', 'biotech'), ('1733', '五鼎', 'biotech'), ('1734', '杏輝', 'biotech'), ('1736', '喬山', 'biotech'), ('1760', '寶齡富錦', 'biotech'), ('1762', '中化生', 'biotech'), ('1783', '和康生', 'biotech'), ('1786', '科妍', 'biotech'), ('1789', '神隆', 'biotech'), ('1795', '美時', 'biotech'), ('3164', '景岳', 'biotech'), ('3705', '永信', 'biotech'), ('4104', '佳醫', 'biotech'), ('4106', '雃博', 'biotech'), ('4108', '懷特', 'biotech'), ('4119', '旭富', 'biotech'), ('4133', '亞諾法', 'biotech'), ('4137', '麗豐-KY', 'biotech'), ('4141', '龍燈-KY', 'biotech'), ('4142', '國光生', 'biotech'), ('4148', '全宇生技-KY', 'biotech'), ('4155', '訊映', 'biotech'), ('4164', '承業醫', 'biotech'), ('4190', '佐登-KY', 'biotech'), ('4737', '華廣', 'biotech'), ('4746', '台耀', 'biotech'), ('6491', '晶碩', 'biotech'), ('6541', '泰福-KY', 'biotech'), ('6598', 'ABC-KY', 'biotech'), ('6666', '羅麗芬-KY', 'biotech')]
# 5
stock_list_finance = [('2801', '彰銀', 'finance'), ('2809', '京城銀', 'finance'), ('2812', '台中銀', 'finance'), ('2816', '旺旺保', 'finance'), ('2820', '華票', 'finance'), ('2823', '中壽', 'finance'), ('2832', '台產', 'finance'), ('2834', '臺企銀', 'finance'), ('2836', '高雄銀', 'finance'), ('2836A', '高雄銀甲特', 'finance'), ('2838', '聯邦銀', 'finance'), ('2838A', '聯邦銀甲特', 'finance'), ('2845', '遠東銀', 'finance'), ('2849', '安泰銀', 'finance'), ('2850', '新產', 'finance'), ('2851', '中再保', 'finance'), ('2852', '第一保', 'finance'), ('2855', '統一證', 'finance'), ('2867', '三商壽', 'finance'), ('2880', '華南金', 'finance'), ('2881', '富邦金', 'finance'), ('2881A', '富邦特', 'finance'), ('2881B', '富邦金乙特', 'finance'), ('2882', '國泰金', 'finance'), ('2882A', '國泰特', 'finance'), ('2882B', '國泰金乙特', 'finance'), ('2883', '開發金', 'finance'), ('2884', '玉山金', 'finance'), ('2885', '元大金', 'finance'), ('2886', '兆豐金', 'finance'), ('2887', '台新金', 'finance'), ('2887E', '台新戊特', 'finance'), ('2887F', '台新戊特二', 'finance'), ('2888', '新光金', 'finance'), ('2888A', '新光金甲特', 'finance'), ('2888B', '新光金乙特', 'finance'), ('2889', '國票金', 'finance'), ('2890', '永豐金', 'finance'), ('2891', '中信金', 'finance'), ('2891B', '中信金乙特', 'finance'), ('2891C', '中信金丙特', 'finance'), ('2892', '第一金', 'finance'), ('2897', '王道銀行', 'finance'), ('2897A', '王道銀甲特', 'finance'), ('5876', '上海商銀', 'finance'), ('5880', '合庫金', 'finance'), ('6005', '群益證', 'finance'), ('6024', '群益期', 'finance')]
# 2330
stock_list_tsmc = [('2330', '台積電', 'stock_market')]

# 股市看漲相關字
keyword_list_stockmart_word_positive = ["升級", "長", "買", "買進", "牛市", "牛", "牛群", "成長", "好", "得到",
                                        "佳", "棒", "讚", "最好", "支撐", "更新", "強", "贏", "利多", "正向",
		                                "潛力","收益", "紅利","成功","贏家","勝利", '看好', '看漲', '回溫',
                                        "反彈", "漲停", "樂觀", "紅", "長紅", "進場", "大漲", "賺", "漲", "高峰", "黃金交叉", "喜",
                                        "帶動", "大賺", "買氣", "優於預期"]

# 股市看衰相關字
keyword_list_stockmart_word_negative = ["降級", "短", "賣", "賣出", "熊市", "熊", "熊群", "蒸發", "壞", "失去",
                                        "差", "爛", "廢", "最差", "賣壓", "保守", "弱", "輸", "利空", "負向",
                                        "阻力", "套牢", "損失", "失敗", "輸家", "慘敗", "不看好", "看衰", "低迷",
                                        "急跌", "跌停", "悲觀", "綠", "慘綠", "出場", "崩盤", "賠", "崩", "谷底", "死亡交叉", "憂",
                                        "韭菜", "慘賠", "收割", "低於預期"]

# read sentiment word base
cvaw4 = pd.read_csv('cvaw4.csv', index_col='Word')
# cvaw4.head()

def iso_date(year, month, day):
    if month < 10:
        month = "0" + str(month)
    if day < 10:
        day = "0" + str(day)
    try:
        create_time = datetime.fromisoformat(f'{year}-{month}-{day}')
    except:
        return None
    else:
        return create_time


def fetch_article_tag(year, month, day, col_name):
    db_mongo = model_mongo.DbWrapperMongo()

    create_time = iso_date(year, month, day)
    query_dict = {"create_time": create_time}
    rows = db_mongo.find(col_name, query_dict)
    rows = [row for row in rows]
    return create_time, rows


def word_count_tag(stock_tuple, rows):
    daily_word_cut = []
    stock_code = stock_tuple[0]
    stock_name = stock_tuple[1]
    article_count = 0
    for row in rows:
        tag_total = row['tag_total']
        word_cut = row['word_cut']  # word_cut
        # print("tag_total, ", tag_total)
        # print("word_cut, ", word_cut)
        if stock_code in tag_total:
            # print('gotcha')
            article_count += 1
            daily_word_cut += word_cut
    # print(f"{stock_name} is analyzed")
    # print("daily_word_cut, ", daily_word_cut)
    seg_counter_total = Counter(daily_word_cut)
    # print("seg_counter_total, ", seg_counter_total)
    # print(f"{article_count} articles counted")

    if stock_code in seg_counter_total.keys():
        stock_code_count = seg_counter_total[stock_code]
        # print(f"{stock_code} count: ", seg_counter_total[stock_code])
    else:
        stock_code_count = 0

    if stock_name in seg_counter_total.keys():
        stock_name_count = seg_counter_total[stock_name]
        # print(f"{stock_name} count: ", seg_counter_total[stock_name])

    else:
        stock_name_count = 0

    stock_count = stock_code_count + stock_name_count
    # print(f"total stock count: ", stock_count)
    return article_count, daily_word_cut, stock_code, stock_count


def word_count_category(rows, category, stock_list_category):
    daily_word_cut_category = []
    article_count_category = 0
    for row in rows:
        if row[f'tag_{category}']:
            daily_word_cut_category += row['word_cut']
            article_count_category += 1
    # print(daily_word_cut_category)
    seg_counter_total = Counter(daily_word_cut_category)
    # print(seg_counter_total)
    # print(f"article_count: {article_count_category}")
    stock_code_count_category = 0
    stock_code_count_category_dict = defaultdict(int)
    for stock_tuple in stock_list_category:
        stock_code = stock_tuple[0]
        stock_name = stock_tuple[1]
        seg_counter_total_words_list = seg_counter_total.keys()
        if stock_code in seg_counter_total_words_list:
            stock_code_count_category_dict[stock_code] += seg_counter_total[stock_code]
            stock_code_count_category += seg_counter_total[stock_code]
        if stock_name in seg_counter_total_words_list:
            stock_code_count_category_dict[stock_code] += seg_counter_total[stock_name]
            stock_code_count_category += seg_counter_total[stock_name]

    # print(f"stock_word_count: {stock_code_count_category}")
    # print(f"stock_code_count_dict: {stock_code_count_category_dict}")
    return article_count_category, daily_word_cut_category, stock_code_count_category, stock_code_count_category_dict


def word_count_daily(rows, stock_list_total):
    daily_word_cut_total = []
    article_count_total = len(rows)
    for row in rows:
        daily_word_cut_total += row['word_cut']

    seg_counter_total = Counter(daily_word_cut_total)

    stock_code_count_total = 0
    stock_code_count_total_dict = defaultdict(int)
    for stock_tuple in stock_list_total:
        stock_code = stock_tuple[0]
        stock_name = stock_tuple[1]
        seg_counter_total_words_list = seg_counter_total.keys()
        if stock_code in seg_counter_total_words_list:
            stock_code_count_total_dict[stock_code] += seg_counter_total[stock_code]
            stock_code_count_total += seg_counter_total[stock_code]
        if stock_name in seg_counter_total_words_list:
            stock_code_count_total_dict[stock_code] += seg_counter_total[stock_name]
            stock_code_count_total += seg_counter_total[stock_name]
    # print(f"article_count: {article_count_total}")
    # print(f"daily_word_cut: {daily_word_cut_total}")
    # print(f"stock_code_count_total: {stock_code_count_total}")
    # print(f"stock_code_count_total_dict: {stock_code_count_total_dict}")
    return article_count_total, daily_word_cut_total, stock_code_count_total, stock_code_count_total_dict


def sentiment_grade_cvaw(seg_words_list):
    sentiment_result = []
    sum_V = 0
    sum_A = 0
    count = 0
    for w in seg_words_list:  # 用文章＋推文的內容去算情感分數
        if w in cvaw4.index:
            sentiment_result.append(w)
            sum_V = sum_V + cvaw4['Valence_Mean'][str(w)]
            sum_A = sum_A + cvaw4['Arousal_Mean'][str(w)]
            count = count + 1
    if count > 0:
        avg_V = sum_V / count
        avg_A = sum_A / count
    else:
        avg_V = 5
        avg_A = 5
    return sentiment_result, sum_V, avg_V, sum_A, avg_A, count


def sentiment_grade_cashtag(seg_words_list):
    sentiment_result = []
    sum_sentiment = 0
    for w in seg_words_list:  # 用文章＋推文的內容去算情感分數
        if w in keyword_list_stockmart_word_positive:
            sentiment_result.append(w)
            sum_sentiment += 1
        elif w in keyword_list_stockmart_word_negative:
            sentiment_result.append(w)
            sum_sentiment -= 1

    return sentiment_result, sum_sentiment


def word_count_total_make_tuple(rows, stock_list_total):
    article_count_total, daily_word_cut_total, stock_code_count_total, stock_code_count_total_dict = word_count_daily(rows, stock_list_total)
    sentiment_result_cvaw_total, sum_V_total, avg_V_total, sum_A_total, avg_A_total, count_total = sentiment_grade_cvaw(daily_word_cut_total)
    sentiment_result_cashtag_total, sum_sentiment_total = sentiment_grade_cashtag(daily_word_cut_total)
    stock_count_tuple_total = (date, SOURCE, '0', stock_code_count_total, article_count_total)
    # print(stock_count_tuple_total)
    stock_code_sentiment_tuple = (date, SOURCE, '0', sum_V_total, avg_V_total, sum_A_total, avg_A_total, sum_sentiment_total)
    # print(stock_code_sentiment_tuple)
    return stock_count_tuple_total, stock_code_sentiment_tuple


def word_count_category_make_tuple(rows, category, stock_list_category):
    category_stock_code = {"electric_car": '1', 'electric': '2', 'sail': '3', 'biotech': '4', 'finance': '5'}
    stock_code = category_stock_code[category]
    article_count_category, daily_word_cut_category, stock_code_count_category, stock_code_count_dict_category = word_count_category(rows, category, stock_list_category)
    sentiment_result_cvaw_category, sum_V_category, avg_V_category, sum_A_category, avg_A_category, count_category = sentiment_grade_cvaw(daily_word_cut_category)
    sentiment_result_cashtag_category, sum_sentiment_category = sentiment_grade_cashtag(daily_word_cut_category)
    stock_count_tuple = (date, SOURCE, stock_code, stock_code_count_category, article_count_category)

    stock_code_sentiment_tuple = (date, SOURCE, stock_code, sum_V_category, avg_V_category, sum_A_category, avg_A_category, sum_sentiment_category)
    # print(stock_code_sentiment_tuple)
    return stock_count_tuple, stock_code_sentiment_tuple


def word_count_tag_make_tuple(rows, stock_tuple):
    article_count_stock, daily_word_cut_stock, stock_code, stock_count = word_count_tag(stock_tuple, rows)
    # calculate sentiment grade
    sentiment_result_cvaw_stock, sum_V_stock, avg_V_stock, sum_A_stock, avg_A_stock, count_stock = sentiment_grade_cvaw(
        daily_word_cut_stock)
    sentiment_result_cashtag_stock, sum_sentiment_stock = sentiment_grade_cashtag(daily_word_cut_stock)
    stock_count_tuple = (date, SOURCE, stock_code, stock_count, article_count_stock)
    # word count sentiment
    # seg_counter_sentiment_cvaw = Counter(sentiment_result_cvaw)
    # seg_counter_sentiment_cashtag = Counter(sentiment_result_cashtag)
    stock_code_sentiment_tuple = (date, SOURCE, stock_code, sum_V_stock, avg_V_stock, sum_A_stock, avg_A_stock, sum_sentiment_stock)
    return stock_count_tuple, stock_code_sentiment_tuple


if __name__ == '__main__':
    start_time = time.time()  # 使用 time 模組的 time 功能 紀錄當時系統時間 從 start_time
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')

    social_volume_tuple_list = []
    sentiment_tuple_list = []
    for year in range(2013, 2012, -1):
        for month in range(1, 13):
            for day in range(1, 32):
                print(f'calculate {year}-{month}-{day}')
                # fetch mongo raw data
                try:
                    date, rows = fetch_article_tag(year, month, day, f'{SOURCE}_stock_tag')
                except:
                    print("no date")
                    continue
                else:
                    # pprint(rows)
                    # total words in day
                    if not date:
                        continue
                    else:
                        # words in day total
                        stock_count_tuple_total, stock_code_sentiment_tuple_total = word_count_total_make_tuple(rows, stock_list_total)
                        social_volume_tuple_list.append(stock_count_tuple_total)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_total)


                        # words in day by category
                        # elctric car
                        stock_count_tuple_electric_car, stock_code_sentiment_tuple_electric_car = word_count_category_make_tuple(rows, 'electric_car', stock_list_electric_car)
                        # print(stock_code_sentiment_tuple_electric_car)
                        social_volume_tuple_list.append(stock_count_tuple_electric_car)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_electric_car)

                        # elctric
                        stock_count_tuple_electric, stock_code_sentiment_tuple_electric = word_count_category_make_tuple(rows, 'electric', stock_list_electric)
                        social_volume_tuple_list.append(stock_count_tuple_electric)
                        # print(stock_code_sentiment_tuple_electric)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_electric)

                        # sail
                        stock_count_tuple_sail, stock_code_sentiment_tuple_sail = word_count_category_make_tuple(rows, 'sail', stock_list_sail)
                        social_volume_tuple_list.append(stock_count_tuple_sail)
                        # print(stock_code_sentiment_tuple_sail)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_sail)

                        # biotech
                        stock_count_tuple_biotech, stock_code_sentiment_tuple_biotech = word_count_category_make_tuple(rows, 'biotech', stock_list_biotech)
                        # print(stock_code_sentiment_tuple_biotech)
                        social_volume_tuple_list.append(stock_count_tuple_biotech)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_biotech)

                        # finance
                        stock_count_tuple_finance, stock_code_sentiment_tuple_finance = word_count_category_make_tuple(rows, 'finance', stock_list_finance)
                        # print(stock_code_sentiment_tuple_finance)
                        social_volume_tuple_list.append(stock_count_tuple_finance)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_finance)


                        # words in day by stock
                        for stock_tuple in stock_list_electric_car:
                            stock_count_tuple_electric_car, stock_code_sentiment_tuple_electric_car = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_electric_car)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_electric_car)

                        for stock_tuple in stock_list_electric:
                            stock_count_tuple_electric, stock_code_sentiment_tuple_electric = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_electric)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_electric)

                        for stock_tuple in stock_list_sail:
                            stock_count_tuple_sail, stock_code_sentiment_tuple_sail = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_sail)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_sail)

                        for stock_tuple in stock_list_biotech:
                            stock_count_tuple_biotech, stock_code_sentiment_tuple_biotech = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_biotech)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_biotech)

                        for stock_tuple in stock_list_finance:
                            stock_count_tuple_finance, stock_code_sentiment_tuple_finance = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_finance)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_finance)

                        for stock_tuple in stock_list_tsmc:
                            stock_count_tuple_tsmc, stock_code_sentiment_tuple_tsmc = word_count_tag_make_tuple(rows, stock_tuple)
                            social_volume_tuple_list.append(stock_count_tuple_tsmc)
                            sentiment_tuple_list.append(stock_code_sentiment_tuple_tsmc)



    print(social_volume_tuple_list)
    print(sentiment_tuple_list)

    stock_list = [s[2] for s in social_volume_tuple_list]
    print(stock_list)

    sql_insert_social_volume = "INSERT INTO `daily_social_volume` (`date`, `source`, `stock_code`, `count`, `article_count`) VALUES (%s, %s, %s, %s, %s)"
    sql_insert_sentiment = "INSERT INTO `daily_sentiment` (`date`, `source`, `stock_code`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    db_mysql.insert_many_tb(sql_insert_social_volume, social_volume_tuple_list)
    db_mysql.insert_many_tb(sql_insert_sentiment, sentiment_tuple_list)

    end_time = time.time()  # 使用 time 模組的 time 功能 紀錄當時系統時間 到 end_time
    print(f'elapsed {end_time - start_time} seconds')

# db.ptt_wc.deleteMany({create_time: {$gte: ISODate("2021-12-01T00:00:00.000+00:00"), $lte: ISODate('2021-12-31T00:00:00.000+00:00')}})

# check primary
# for stock_code in ['0', '1', '1611', '1723', '2308', '2371', '4721', '4738', '4739', '4999', '5227', '6443', '8038', '8358', '1503', '1519', '1533', '1536', '1537', '1587', '2301', '2317', '2357', '2392', '2421', '2459', '2483', '3023', '3665', '4503', '5233', '5439', '6121', '6275', '6282', '8109', '8171', '8183', '1599', '1729', '2237', '8933', '8937', '9914', '0', '1', '1611', '1723', '2308', '2371', '4721', '4738', '4739', '4999', '5227', '6443', '8038', '8358', '1503', '1519', '1533', '1536', '1537', '1587', '2301', '2317', '2357', '2392', '2421', '2459', '2483', '3023', '3665', '4503', '5233', '5439', '6121', '6275', '6282', '8109', '8171', '8183', '1599', '1729', '2237', '8933', '8937', '9914']:
    #     result = db_mysql.query_tb_all("SELECT `stock_code` from stocks where `stock_code` = '{}'".format(stock_code))
    #     print(result)