from config import SYSPATH
import sys
sys.path.insert(0, SYSPATH)
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
        db_mysql.create_tb_stock_price_view()

    def test_insert_stock_price_view(self):
        with open('tests/data/stock_price_view_mock.csv') as f:
            mock_stock_price = [tuple(line) for line in csv.reader(f)]

        db_mysql = model_mysql.DbWrapperMysql()
        sql_insert_stock_price_view = model_mysql_query.sql_insert_stock_price_view
        db_mysql.insert_many_tb(sql_insert_stock_price_view, mock_stock_price)

    def test_fetch_stock_price(self):
        stock_code = '2603'

        params = {
            'end-date': '2021-11-23'
        }

        stock_price_fetch = StockSentimentFetch()
        daily_stock_price = stock_price_fetch.fetch_stock_price(stock_code)
        # print(daily_stock_price)

        assert daily_stock_price['date'][0] == params['end-date']

    # def test_drop_tb(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.drop_tb('stock_price_view')
        db_mysql.close_db()
        print('fetch stock_price test is finished')
        print('db is cleaned')
