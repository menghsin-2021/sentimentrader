import sys
sys.path.insert(0, '/Users/menghsin/Desktop/coding/AppWorks-school/sentimentrader/flask_app')
import csv
from utils import SocialVolumeFetch
from model import model_mysql, model_mysql_query

class TestFetchSocialVolume(object):
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
        category = None
        source = None
        duration = None

        params = {
            'stock_name_code': ['華航, 2610', '長榮, 2603', '長榮航, 2618', '台積電, 2330', '宏達電, 2498', '萬海, 2615', '陽明, 2609', '南電, 8046', '友達, 2409', '欣興, 3037'],
            'stock_count': [203, 101, 95, 32, 36, 35, 28, 20, 17, 16],
            'article_count': [24, 20, 17, 16, 10, 8, 11, 7, 8, 8],
        }

        social_volume_fetch = SocialVolumeFetch()
        stock_name_code, stock_count, article_count = social_volume_fetch.social_volume(category, source, duration)

        assert stock_name_code == params['stock_name_code']
        assert stock_count == params['stock_count']
        assert article_count == params['article_count']

    def test_drop_tb(self):
        db_mysql = model_mysql.DbWrapperMysql()
        db_mysql.drop_tb('social_volume_view')
        db_mysql.close_db()
        print('social_volume test is finished')
        print('db is cleaned')
