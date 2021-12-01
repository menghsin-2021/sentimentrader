from config import SYSPATH
import sys
sys.path.insert(0, SYSPATH)
import csv
from utils import SocialVolumeFetch
from model import model_mysql, model_mysql_query

class TestSocialVolumeFetch(object):
    def test_argument(self, db_env):
        print(model_mysql.DBNAME)
        assert db_env == 'test'
        assert model_mysql.DBNAME == 'sentimentrader_test'

    def test_create_db(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.create_tb_social_volume_view()

    def test_insert_social_volume_view(self):
        with open('tests/data/social_volume_view_mock.csv') as f:
            mock_social_volume = [tuple(line) for line in csv.reader(f)]
        # print(mock_social_volume)

        db_mysql = model_mysql.DbWrapperMysql()
        sql_insert_social_volume_view = model_mysql_query.sql_insert_social_volume_view
        db_mysql.insert_many_tb(sql_insert_social_volume_view, mock_social_volume)

    def test_fetch_social_volume(self):
        category = 'electric'
        source = 'ptt'
        duration = 'daily'

        params = {
            'stock_name_code': ['宏達電, 2498', '南電, 8046', '友達, 2409', '欣興, 3037', '鴻海, 2317', '光磊, 2340', '全新, 2455', '奇鋐, 3017', '譁裕, 3419', '凱美, 2375'],
            'stock_count': [36, 20, 17, 16, 16, 14, 13, 12, 12, 9],
            'article_count': [10, 7, 8, 8, 7, 6, 7, 7, 2, 4],
        }

        social_volume_fetch = SocialVolumeFetch()
        stock_name_code, stock_count, article_count = social_volume_fetch.social_volume(category, source, duration)

        print(stock_name_code, stock_count, article_count)

        assert stock_name_code == params['stock_name_code']
        assert stock_count == params['stock_count']
        assert article_count == params['article_count']

    def test_drop_tb(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.drop_tb('social_volume_view')
        db_mysql.close_db()
        print('social_volume test is finished')
        print('db is cleaned')
