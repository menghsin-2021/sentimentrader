import sys
sys.path.insert(0, '/Users/menghsin/Desktop/coding/AppWorks-school/sentimentrader/flask_app')
import csv
from utils import StockSentimentFetch
from model import model_mysql, model_mysql_query

class TestStockSentimentFetch(object):
    def test_argument(self, db_env):
        print(model_mysql.DBNAME)
        assert db_env == 'test'
        assert model_mysql.DBNAME == 'sentimentrader_test'

    def test_create_db(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.create_tb_sentiment_view()

    def test_insert_sentiment_view(self):
        with open('tests/data/sentiment_view_mock.csv') as f:
            mock_sentiment = [tuple(line) for line in csv.reader(f)]
        # print(mock_sentiment)

        db_mysql = model_mysql.DbWrapperMysql()
        sql_insert_sentiment_view = model_mysql_query.sql_insert_sentiment_view
        db_mysql.insert_many_tb(sql_insert_sentiment_view, mock_sentiment)

    def test_fetch_sentiment(self):
        source = 'ptt'
        stock_code = '2603'

        params = {
            'avg_valence_now': 51
        }

        stock_sentiment_fetch = StockSentimentFetch()
        daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, stock_code)

        assert daily_sentiment['avg_valence_now'] == params['avg_valence_now']

    # def test_drop_tb(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.drop_tb('sentiment_view')
        db_mysql.close_db()
        print('fetch sentiment test is finished')
        print('db is cleaned')
