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

def fetch_daily_data_ptt(year, month, day):
    db_mongo = model_mongo.DbWrapperMongo()
    if day < 10:
        query_dict = {'create_time': {'$regex': f"{month}  {day}(.*){year}"}}
        col_name = 'ptt'
        rows = db_mongo.find(col_name, query_dict)
        rows = [row for row in rows]
        return rows
    elif day >= 10:
        query_dict = {'create_time': {'$regex': f"{month} {day}(.*){year}"}}
        col_name = 'ptt'
        rows = db_mongo.find(col_name, query_dict)
        rows = [row for row in rows]
        return rows


def daily_content_list(rows):
    all_title_list = [row['title'] for row in rows]
    all_article_list = [row['content'].replace("\n", "") for row in rows]
    all_responses = [row['all_response_list'] for row in rows]

    all_response_list = []
    for responses in all_responses:
        all_response_list.append(''.join(responses))

    daily_content_list = [''.join(content) for content in list(zip(all_title_list, all_article_list, all_response_list))]
    return daily_content_list


def daily_text_ptt(rows):
    all_article_text = ''.join([row['content'].replace("\n", "") for row in rows])

    all_responses = [row['all_response_list'] for row in rows]
    response_list = []
    for responses in all_responses:
        for response in responses:
            response_list.append(response)

    all_response_text = ''.join(response_list)

    all_article_response_text = all_article_text + all_response_text
    return all_article_text, all_response_text, all_article_response_text


def tag_stocks_list(stock_list, seg_stop_words_list_total):
    tag_stocks_list = []
    for n in range(len(stock_list)):
        stock_code = stock_list[n][0]
        stock_name = stock_list[n][1]
        if stock_code in seg_stop_words_list_total or stock_name in seg_stop_words_list_total:
            tag_stocks_list.append(stock_code)
    return tag_stocks_list

if __name__ == '__main__':
    month_dict = {1: ["Jan", '01'], 2: ["Feb", '02'], 3: ["Mar", '03'], 4: ["Apr", '04'],
                  5: ["May", '05'], 6: ["Jun", '06'], 7: ["Jul", '07'], 8: ["Aug", '08'],
                  9: ["Sep", '09'], 10: ["Oct", '10'], 11: ["Nov", '11'], 12: ["Dec", '12']}

    json_dict_list = []
    for k in range(2021, 2020, -1):
        year_fetch = k
        for j in range(10, 11):
            month_fetch = month_dict[j][0]
            for i in range(19, 20):
                day_fetch = i
                print(f'calculate {year_fetch}-{month_fetch}-{day_fetch}')
                # fetch mongo raw data
                try:
                    rows = fetch_daily_data_ptt(year_fetch, month_fetch, day_fetch)
                except:
                    print("no date")
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
                        electric_car_tag_stocks_list = tag_stocks_list(stock_list_electric_car, seg_stop_words_list_total)
                        electric_tag_stocks_list = tag_stocks_list(stock_list_electric, seg_stop_words_list_total)
                        sail_tag_stocks_list = tag_stocks_list(stock_list_sail, seg_stop_words_list_total)
                        biotech_tag_stocks_list = tag_stocks_list(stock_list_biotech, seg_stop_words_list_total)
                        finance_tag_stocks_list = tag_stocks_list(stock_list_finance, seg_stop_words_list_total)
                        tsmc_tag_stocks_list = tag_stocks_list(stock_list_tsmc, seg_stop_words_list_total)
                        total_tag_stocks_list = electric_car_tag_stocks_list + electric_tag_stocks_list + sail_tag_stocks_list + biotech_tag_stocks_list + finance_tag_stocks_list + tsmc_tag_stocks_list

                        # formate json
                        year_save = k
                        month_save = month_dict[j][1]
                        day_save = i
                        if day_save < 10:
                            day_save = f"0{i}"
                        try:
                            create_time = datetime.fromisoformat(f'{year_save}-{month_save}-{day_save}')
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


    # save to mongo
    db_mongo = model_mongo.DbWrapperMongo()
    col_name = "ptt_stock_tag"
    # col_name = "test"
    db_mongo.insert_many(col_name, json_dict_list)




# db.ptt_wc.deleteMany({create_time: {$gte: ISODate("2021-12-01T00:00:00.000+00:00"), $lte: ISODate('2021-12-31T00:00:00.000+00:00')}})