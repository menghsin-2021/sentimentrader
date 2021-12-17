from pymongo import MongoClient
from urllib.parse import quote_plus
import config

# 設定 mongo_db 連線資料
MONGO_USER = config.MONGO_USER
MONGO_PASSWORD = config.MONGO_PASSWORD
MONGO_HOST = config.MONGO_HOST
MONGO_DBNAME = config.MONGO_DBNAME
uri = "mongodb://%s:%s@%s/%s?retryWrites=true&w=majority" % (quote_plus(MONGO_USER), quote_plus(MONGO_PASSWORD), MONGO_HOST, MONGO_DBNAME)

class DbWrapperMongo:
    def __init__(self):
        self.client = MongoClient(uri, 27017)
        self.db_forum = self.client.forum
        self.db_news = self.client.news
        self.db_word_count = self.client.word_count
        self.db_article_tag = self.client.article_tag
        self.db_test_pipeline = self.client.test_pipeline
        self.db_test = self.client.test

        self.col_ptt = self.db_forum.ptt
        self.col_mobile = self.db_forum.mobile
        self.col_moneydj = self.db_news.moneydj
        self.col_cnyes = self.db_news.cnyes
        self.col_ptt_wc = self.db_word_count.ptt_wc
        self.col_cnyes_wc = self.db_word_count.cnyes_wc
        self.col_test = self.db_test.test
        self.col_ptt_stock_tag = self.db_article_tag.ptt_stock_tag
        self.col_cnyes_stock_tag = self.db_article_tag.cnyes_stock_tag
        self.col_stabilization = self.db_test_pipeline.stabilization

    def insert_one(self, col_name, dict):
        if col_name == 'ptt':
            self.col_ptt.insert_one(dict)

        if col_name == 'mobile':
            self.col_mobile.insert_one(dict)

        if col_name == 'moneydj':
            self.col_moneydj.insert_one(dict)

        if col_name == 'cnyes':
            self.col_cnyes.insert_one(dict)

        if col_name == 'ptt_wc':
            self.col_ptt_wc.insert_one(dict)

        if col_name == 'cnyes_wc':
            self.col_cnyes_wc.insert_one(dict)

        if col_name == 'stabilization':
            self.col_stabilization.insert_one(dict)

        if col_name == 'test':
            self.col_test.insert_one(dict)

    def insert_many(self, col_name, dict_list):
        if col_name == "ptt":
            self.col_ptt.insert_many(dict_list)

        if col_name == "mobile01":
            self.col_mobile.insert_many(dict_list)

        if col_name == 'moneydj':
            self.col_moneydj.insert_many(dict_list)

        if col_name == 'ptt_wc':
            self.col_ptt_wc.insert_many(dict_list)

        if col_name == 'cnyes_wc':
            self.col_cnyes_wc.insert_many(dict_list)

        if col_name == 'test':
            self.col_test.insert_many(dict_list)

        if col_name == 'ptt_stock_tag':
            self.col_ptt_stock_tag.insert_many(dict_list)

        if col_name == 'cnyes_stock_tag':
            self.col_cnyes_stock_tag.insert_many(dict_list)

    def find(self, col_name, query_dict):
        if col_name == 'ptt':
            rows = self.col_ptt.find(query_dict)
            return rows

        if col_name == 'moneydj':
            rows = self.col_moneydj.find(query_dict)
            return rows

        if col_name == 'cnyes':
            rows = self.col_cnyes.find(query_dict)
            return rows

        if col_name == 'ptt_wc':
            rows = self.col_ptt_wc.find(query_dict)
            return rows

        if col_name == 'cnyes_wc':
            rows = self.col_cnyes_wc.find(query_dict)
            return rows

        if col_name == 'ptt_stock_tag':
            rows = self.col_ptt_stock_tag.find(query_dict)
            return rows

        if col_name == 'cnyes_stock_tag':
            rows = self.col_cnyes_stock_tag.find(query_dict)
            return rows

        if col_name == 'test':
            rows = self.col_test.find(query_dict)
            return rows

        if col_name == 'stabilization':
            rows = self.col_stabilization.find(query_dict)
            return rows

    def find_sorted(self, col_name, query_dict, field, direction):
        if col_name == 'stabilization':
            rows = self.col_stabilization.find(query_dict).sort(field, direction)
            return rows