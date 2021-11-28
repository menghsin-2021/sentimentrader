# coding=utf-8
import model_mysql
import model_mongo
from datetime import datetime
import pandas as pd
from collections import Counter, defaultdict
import time
import stock_list

SOURCE = 'ptt'
# SOURCE = 'cnyes'

stock_list_electric_car = stock_list.stock_list_electric_car
stock_list_electric = stock_list.stock_list_electric
stock_list_sail = stock_list.stock_list_sail
stock_list_biotech = stock_list.stock_list_biotech
stock_list_finance = stock_list.stock_list_finance
stock_list_tsmc = stock_list.stock_list_tsmc

# stock market key words
keyword_list_stockmart_word_positive = stock_list.keyword_list_stockmart_word_positive
keyword_list_stockmart_word_negative = stock_list.keyword_list_stockmart_word_negative


# read sentiment word base
cvaw4 = pd.read_csv('cvaw4.csv', index_col='Word')

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
        word_cut = row['word_cut']
        if stock_code in tag_total:
            article_count += 1
            daily_word_cut += word_cut
    seg_counter_total = Counter(daily_word_cut)

    if stock_code in seg_counter_total.keys():
        stock_code_count = seg_counter_total[stock_code]
    else:
        stock_code_count = 0

    if stock_name in seg_counter_total.keys():
        stock_name_count = seg_counter_total[stock_name]

    else:
        stock_name_count = 0

    stock_count = stock_code_count + stock_name_count
    return article_count, daily_word_cut, stock_code, stock_count


def word_count_category(rows, category, stock_list_category):
    daily_word_cut_category = []
    article_count_category = 0
    for row in rows:
        if row[f'tag_{category}']:
            daily_word_cut_category += row['word_cut']
            article_count_category += 1
    seg_counter_total = Counter(daily_word_cut_category)
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
    return article_count_total, daily_word_cut_total, stock_code_count_total, stock_code_count_total_dict


def sentiment_grade_cvaw(seg_words_list):
    sentiment_result = []
    sum_V = 0
    sum_A = 0
    count = 0
    for w in seg_words_list:
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
    for w in seg_words_list:
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
    stock_code_sentiment_tuple = (date, SOURCE, '0', sum_V_total, avg_V_total, sum_A_total, avg_A_total, sum_sentiment_total)
    return stock_count_tuple_total, stock_code_sentiment_tuple


def word_count_category_make_tuple(rows, category, stock_list_category):
    category_stock_code = {"electric_car": '1', 'electric': '2', 'sail': '3', 'biotech': '4', 'finance': '5'}
    stock_code = category_stock_code[category]
    article_count_category, daily_word_cut_category, stock_code_count_category, stock_code_count_dict_category = word_count_category(rows, category, stock_list_category)
    sentiment_result_cvaw_category, sum_V_category, avg_V_category, sum_A_category, avg_A_category, count_category = sentiment_grade_cvaw(daily_word_cut_category)
    sentiment_result_cashtag_category, sum_sentiment_category = sentiment_grade_cashtag(daily_word_cut_category)
    stock_count_tuple = (date, SOURCE, stock_code, stock_code_count_category, article_count_category)

    stock_code_sentiment_tuple = (date, SOURCE, stock_code, sum_V_category, avg_V_category, sum_A_category, avg_A_category, sum_sentiment_category)
    return stock_count_tuple, stock_code_sentiment_tuple


def word_count_tag_make_tuple(rows, stock_tuple):
    article_count_stock, daily_word_cut_stock, stock_code, stock_count = word_count_tag(stock_tuple, rows)
    # calculate sentiment grade
    sentiment_result_cvaw_stock, sum_V_stock, avg_V_stock, sum_A_stock, avg_A_stock, count_stock = sentiment_grade_cvaw(
        daily_word_cut_stock)
    sentiment_result_cashtag_stock, sum_sentiment_stock = sentiment_grade_cashtag(daily_word_cut_stock)
    stock_count_tuple = (date, SOURCE, stock_code, stock_count, article_count_stock)
    # word count sentiment
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
                        social_volume_tuple_list.append(stock_count_tuple_electric_car)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_electric_car)

                        # elctric
                        stock_count_tuple_electric, stock_code_sentiment_tuple_electric = word_count_category_make_tuple(rows, 'electric', stock_list_electric)
                        social_volume_tuple_list.append(stock_count_tuple_electric)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_electric)

                        # sail
                        stock_count_tuple_sail, stock_code_sentiment_tuple_sail = word_count_category_make_tuple(rows, 'sail', stock_list_sail)
                        social_volume_tuple_list.append(stock_count_tuple_sail)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_sail)

                        # biotech
                        stock_count_tuple_biotech, stock_code_sentiment_tuple_biotech = word_count_category_make_tuple(rows, 'biotech', stock_list_biotech)
                        social_volume_tuple_list.append(stock_count_tuple_biotech)
                        sentiment_tuple_list.append(stock_code_sentiment_tuple_biotech)

                        # finance
                        stock_count_tuple_finance, stock_code_sentiment_tuple_finance = word_count_category_make_tuple(rows, 'finance', stock_list_finance)
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


    stock_list = [s[2] for s in social_volume_tuple_list]

    sql_insert_social_volume = "INSERT INTO `daily_social_volume` (`date`, `source`, `stock_code`, `count`, `article_count`) VALUES (%s, %s, %s, %s, %s)"
    sql_insert_sentiment = "INSERT INTO `daily_sentiment` (`date`, `source`, `stock_code`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    db_mysql.insert_many_tb(sql_insert_social_volume, social_volume_tuple_list)
    db_mysql.insert_many_tb(sql_insert_sentiment, sentiment_tuple_list)
