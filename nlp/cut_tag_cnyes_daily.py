import jieba
import model_mongo
from datetime import datetime
import stock_list

stock_list_electric_car = stock_list.stock_list_electric_car
stock_list_electric = stock_list.stock_list_electric
stock_list_sail = stock_list.stock_list_sail
stock_list_biotech = stock_list.stock_list_biotech
stock_list_finance = stock_list.stock_list_finance
stock_list_tsmc = stock_list.stock_list_tsmc


def get_today():
    today_strftime = datetime.today().strftime('%Y-%m-%d')
    year = int(today_strftime.split('-')[0])
    month = int(today_strftime.split('-')[1])
    day = int(today_strftime.split('-')[2])

    return year, month, day


def fetch_daily_data_cnyes(year, month, day):
    db_mongo = model_mongo.DbWrapperMongo()
    if month < 10:
        month = f"0{month}"
    if day < 10:
        day = f"0{day}"
    query_dict = {'date': {'$regex': f"{year}/{month}/{day}"}}
    col_name = 'cnyes'
    rows = db_mongo.find(col_name, query_dict)
    rows = [row for row in rows]
    return rows


def daily_content_list(rows):
    all_title_list = [row['title'] for row in rows]
    all_article_list = [row['content'].replace("\n", "") for row in rows]
    daily_content_list = [''.join(content) for content in list(zip(all_title_list, all_article_list))]
    return daily_content_list


def tag_stocks_list(stock_list, seg_stop_words_list_total):
    tag_stocks_list = []
    for n in range(len(stock_list)):
        stock_code = stock_list[n][0]
        stock_name = stock_list[n][1]
        if stock_code in seg_stop_words_list_total or stock_name in seg_stop_words_list_total:
            tag_stocks_list.append(stock_code)
    return tag_stocks_list


if __name__ == '__main__':
    year, month, day = get_today()
    json_dict_list = []
    for k in range(year, year + 1):
        for j in range(month, month + 1):
            for i in range(day, day + 1):
                year_fetch = k
                month_fetch = j
                day_fetch = i
                print(f'calculate {year_fetch}-{month_fetch}-{day_fetch}')
                try:
                    # fetch mongo raw data
                    rows = fetch_daily_data_cnyes(year_fetch, month_fetch, day_fetch)

                except:
                    print(f'{year_fetch}-{month_fetch}-{day_fetch} no date')
                    continue

                else:
                    # aggregate text
                    content_list = daily_content_list(rows)

                    # seg text to word
                    jieba.dt.cache_file = 'jieba.cache.new'
                    for content in content_list:
                        seg_list_total = jieba.cut(content)
                        # print("|".join(seg_list_total))

                        # loading stop word
                        with open(file='stop_words.txt', mode='r', encoding='utf-8') as file:
                            stop_words = file.read().split('\n')

                        # seg text by stop word
                        seg_stop_words_list_total = [term for term in seg_list_total if term not in stop_words]

                        # tag stocks
                        electric_car_tag_stocks_list = tag_stocks_list(stock_list_electric_car,
                                                                       seg_stop_words_list_total)
                        electric_tag_stocks_list = tag_stocks_list(stock_list_electric, seg_stop_words_list_total)
                        sail_tag_stocks_list = tag_stocks_list(stock_list_sail, seg_stop_words_list_total)
                        biotech_tag_stocks_list = tag_stocks_list(stock_list_biotech, seg_stop_words_list_total)
                        finance_tag_stocks_list = tag_stocks_list(stock_list_finance, seg_stop_words_list_total)
                        tsmc_tag_stocks_list = tag_stocks_list(stock_list_tsmc, seg_stop_words_list_total)
                        total_tag_stocks_list = electric_car_tag_stocks_list + electric_tag_stocks_list + sail_tag_stocks_list + biotech_tag_stocks_list + finance_tag_stocks_list + tsmc_tag_stocks_list

                        year_fetch = k
                        month_fetch = j
                        day_fetch = i

                        # create time
                        if month_fetch < 10:
                            month_fetch = f"0{month_fetch}"

                        if day_fetch < 10:
                            day_fetch = f"0{day_fetch}"

                        try:
                            create_time = datetime.fromisoformat(f'{year_fetch}-{month_fetch}-{day_fetch}')

                        except:
                            continue
                        else:
                            json_dict = {
                                'create_time': create_time,
                                'word_cut': seg_stop_words_list_total,
                                'tag_total': total_tag_stocks_list,
                                'tag_electric_car': electric_car_tag_stocks_list,
                                'tag_electric': electric_tag_stocks_list,
                                'tag_sail': sail_tag_stocks_list,
                                'tag_biotech': biotech_tag_stocks_list,
                                'tag_finance': finance_tag_stocks_list,
                                'tag_tsmc': tsmc_tag_stocks_list
                            }
                            json_dict_list.append(json_dict)


    # # save to mongo
    db_mongo = model_mongo.DbWrapperMongo()
    col_name = "cnyes_stock_tag"
    # col_name = "test"
    db_mongo.insert_many(col_name, json_dict_list)
