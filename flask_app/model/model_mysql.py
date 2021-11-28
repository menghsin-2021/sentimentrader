import pymysql.cursors
import pymysql
import config
from sqlalchemy import create_engine

# db var
DBHOST = config.DBHOST
DBUSER = config.DBUSER
DBPASSWORD = config.DBPASSWORD
DBNAME = config.DBNAME


tb_name_daily_stock_price = 'daily_stock_price'
tb_name_daily_sentiment = 'daily_sentiment'
tb_name_daily_social_volume = 'daily_social_volume'
tb_name_stocks = 'stocks'
tb_name_user = 'user'
tb_name_strategy_backtest = 'strategy_backtest'


# for test
tb_name_social_volume_view = 'social_volume_view'
tb_name_sentiment_view = 'sentiment_view'
tb_name_stock_price_view = 'stock_price_view'

# create table list
create_sql_format_stocks = {
    "stocks": "CREATE TABLE IF NOT EXISTS {}( \
               `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL, \
               `stock_name` varchar(255) COLLATE utf8mb4_bin NOT NULL, \
               `category` varchar(255) COLLATE utf8mb4_bin NOT NULL, \
               PRIMARY KEY (`stock_code`), \
               INDEX (`stock_name`), INDEX (`category`) \
               )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_stocks)
    }

create_sql_format_stock_price = {
    "daily_stock_price": "CREATE TABLE IF NOT EXISTS {}( \
                `date` DATETIME COLLATE utf8mb4_bin NOT NULL , \
                `open` float COLLATE utf8mb4_bin NOT NULL , \
                `close` float COLLATE utf8mb4_bin NOT NULL , \
                `low` float COLLATE utf8mb4_bin NOT NULL, \
                `high` float COLLATE utf8mb4_bin NOT NULL, \
                `volume` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL, \
                INDEX (`date`), INDEX (`stock_code`), \
                FOREIGN KEY (`stock_code`) REFERENCES stocks(stock_code) \
                )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_daily_stock_price),

    }

create_sql_format_sentiment = {
    "daily_sentiment": "CREATE TABLE IF NOT EXISTS {}( \
                         `id` BIGINT COLLATE utf8mb4_bin NOT NULL AUTO_INCREMENT, \
                         `date` DATETIME COLLATE utf8mb4_bin NOT NULL, \
                         `source` varchar(255) COLLATE utf8mb4_bin NOT NULL , \
                         `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL , \
                         `sum_valence` float COLLATE utf8mb4_bin, \
                         `avg_valence` float COLLATE utf8mb4_bin, \
                         `sum_arousal` float COLLATE utf8mb4_bin, \
                         `avg_arousal` float COLLATE utf8mb4_bin, \
                         `sum_sentiment` float COLLATE utf8mb4_bin, \
                         PRIMARY KEY (`id`), \
                         INDEX (`date`), INDEX (`source`), \
                         FOREIGN KEY (`stock_code`) REFERENCES stocks(stock_code) \
                         )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_daily_sentiment),
    }

create_sql_format_social_volume = {
    "daily_social_volume": "CREATE TABLE IF NOT EXISTS {}( \
                            `id` BIGINT COLLATE utf8mb4_bin NOT NULL AUTO_INCREMENT, \
                            `date` DATETIME COLLATE utf8mb4_bin NOT NULL , \
                            `source` varchar(255) COLLATE utf8mb4_bin NOT NULL , \
                            `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL , \
                            `count` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                            `article_count` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                            PRIMARY KEY (`id`), \
                            INDEX (`date`), INDEX (`source`), INDEX (`stock_code`), \
                            FOREIGN KEY (`stock_code`) REFERENCES stocks(stock_code) \
                            )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_daily_social_volume),
    }

create_sql_format_user = {
    "user": "CREATE TABLE IF NOT EXISTS {}( \
                     `id` BIGINT COLLATE utf8mb4_bin NOT NULL AUTO_INCREMENT, \
                     `name` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL, \
                     `email` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL, \
                     `password` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL, \
                     `password_salt` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL, \
                     `access_token` TEXT COLLATE utf8mb4_bin NOT NULL, \
                     `access_expired` int(11) COLLATE utf8mb4_bin NOT NULL, \
                     PRIMARY KEY (`id`), \
                     INDEX (`name`), INDEX (`email`)\
                     )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_user),
}

create_sql_format_strategy = {
    "strategy_backtest": "CREATE TABLE IF NOT EXISTS {}( \
                `id` BIGINT COLLATE utf8mb4_bin NOT NULL AUTO_INCREMENT, \
                `user_id` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL, \
                `start_date` text COLLATE utf8mb4_bin NOT NULL, \
                `end_date` text COLLATE utf8mb4_bin NOT NULL, \
                `strategy_line` text COLLATE utf8mb4_bin NOT NULL, \
                `strategy_in` text COLLATE utf8mb4_bin, \
                `strategy_in_para` float COLLATE utf8mb4_bin, \
                `strategy_out` text COLLATE utf8mb4_bin, \
                `strategy_out_para` float COLLATE utf8mb4_bin, \
                `strategy_sentiment` text COLLATE utf8mb4_bin, \
                `source` text COLLATE utf8mb4_bin, \
                `sentiment_para_more` float COLLATE utf8mb4_bin, \
                `sentiment_para_less` float COLLATE utf8mb4_bin, \
                `seed_money` text COLLATE utf8mb4_bin NOT NULL, \
                `discount` text COLLATE utf8mb4_bin NOT NULL, \
                `total_buy_count` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `total_sell_count` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `total_return_rate` float COLLATE utf8mb4_bin NOT NULL, \
                `highest_return` float COLLATE utf8mb4_bin NOT NULL, \
                `lowest_return` float COLLATE utf8mb4_bin NOT NULL, \
                `total_win` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `total_lose` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `total_trade` BIGINT COLLATE utf8mb4_bin NOT NULL, \
                `win_rate` float COLLATE utf8mb4_bin NOT NULL, \
                `avg_return_rate` float COLLATE utf8mb4_bin NOT NULL, \
                `irr` float COLLATE utf8mb4_bin NOT NULL, \
                `file_path` text COLLATE utf8mb4_bin NOT NULL, \
                `create_date` text COLLATE utf8mb4_bin NOT NULL, \
                PRIMARY KEY (`id`), \
                FOREIGN KEY (`user_id`) REFERENCES user(id), \
                FOREIGN KEY (`stock_code`) REFERENCES stocks(stock_code) \
                )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_strategy_backtest)
}


# for test
create_sql_format_social_volume_view = {
"social_volume_view": "CREATE TABLE IF NOT EXISTS {} ( \
                        `date` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL, \
                        `source` varchar(255) COLLATE utf8mb4_bin NOT NULL DEFAULT '', \
                        `category` varchar(255) COLLATE utf8mb4_bin NOT NULL DEFAULT '', \
                        `stock_code` varchar(255) COLLATE utf8mb4_bin NOT NULL DEFAULT '', \
                        `stock_name` varchar(255) COLLATE utf8mb4_bin NOT NULL DEFAULT '', \
                        `count` decimal(41,0) DEFAULT NULL, \
                        `article_count` decimal(41,0) DEFAULT NULL, \
                        `duration` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '', \
                        KEY `category` (`category`), \
                        KEY `duration` (`duration`) \
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_social_volume_view)
}

create_sql_format_sentiment_view = {
"sentiment_view": "CREATE TABLE IF NOT EXISTS {} ( \
                   `days` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL, \
                   `source` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                   `stock_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                   `stock_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                   `category` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                   `sum_valence` float DEFAULT NULL, \
                   `avg_valence` double DEFAULT NULL, \
                   `sum_arousal` float DEFAULT NULL, \
                   `avg_arousal` double DEFAULT NULL, \
                   `sum_sentiment` float DEFAULT NULL, \
                   KEY `days` (`days`), \
                   KEY `source` (`source`), \
                   KEY `stock_code` (`stock_code`), \
                   KEY `stock_name` (`stock_name`), \
                   KEY `category` (`category`), \
                   KEY `source_2` (`source`,`stock_code`), \
                   KEY `days_2` (`days`,`source`,`stock_code`) \
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_sentiment_view)
}

create_sql_format_stock_price_view = {
"stock_price_view": "CREATE TABLE IF NOT EXISTS {} ( \
                     `days` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL, \
                     `stock_code` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL, \
                     `stock_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                     `category` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, \
                     `open` float DEFAULT NULL, \
                     `low` float DEFAULT NULL, \
                     `high` float DEFAULT NULL, \
                     `close` float DEFAULT NULL, \
                     `volume` bigint DEFAULT NULL, \
                     KEY `days` (`days`), \
                     KEY `stock_code` (`stock_code`), \
                     KEY `stock_name` (`stock_name`), \
                     KEY `category` (`category`), \
                     KEY `category_2` (`category`,`stock_code`), \
                     KEY `days_2` (`days`,`category`,`stock_code`) \
                     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;".format(tb_name_stock_price_view)
}

class DbWrapperMysql:
    def __init__(self):
        self.connect_db = pymysql.connect(host=DBHOST,
                                    port=3306,
                                    user=DBUSER,
                                    password=DBPASSWORD,
                                    database=DBNAME)

        self.cursor = self.connect_db.cursor()

    def create_tb(self, sql_create_tb, tb_name):
        tables = {}
        tables[tb_name] = sql_create_tb

        for table_name in tables:
            table_description = tables[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                self.cursor.execute(table_description)
                print("OK")
            except Exception as e:
                print("Exeception occured:{}".format(e))

    def create_tb_stocks(self):
        self.create_tb(create_sql_format_stocks['stocks'], tb_name_stocks)

    def create_tb_stock_price(self):
        self.create_tb(create_sql_format_stock_price['daily_stock_price'], tb_name_daily_stock_price)

    def create_tb_sentiment(self):
        self.create_tb(create_sql_format_sentiment['daily_sentiment'], tb_name_daily_sentiment)


    def create_tb_social_volume(self):
        self.create_tb(create_sql_format_social_volume['daily_social_volume'], tb_name_daily_social_volume)

    def create_tb_user(self):
        self.create_tb(create_sql_format_user['user'], tb_name_user)

    def create_tb_strategy(self):
        self.create_tb(create_sql_format_strategy['strategy_backtest'], tb_name_strategy_backtest)

    def create_tb_social_volume_view(self):
        self.create_tb(create_sql_format_social_volume_view['social_volume_view'], tb_name_social_volume_view)

    def create_tb_sentiment_view(self):
        self.create_tb(create_sql_format_sentiment_view['sentiment_view'], tb_name_sentiment_view)

    def create_tb_stock_price_view(self):
        self.create_tb(create_sql_format_stock_price_view['stock_price_view'], tb_name_stock_price_view)

    def create_tb_all(self):
        self.create_tb_stocks()
        self.create_tb_stock_price()
        self.create_tb_sentiment()
        self.create_tb_social_volume()
        self.create_tb_user()
        self.create_tb_strategy()

    def insert_tb(self, sql_insert, insert_tuple):
        self.cursor.execute(sql_insert, insert_tuple)
        self.connect_db.commit()

    def insert_many_tb(self, sql_insert, insert_tuple_list):
        self.cursor.executemany(sql_insert, insert_tuple_list)
        self.connect_db.commit()

    def query_tb_all(self, sql_query, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_query, query_tuple)
            result = self.cursor.fetchall()
        else:
            self.cursor.execute(sql_query)
            result = self.cursor.fetchall()
        return result

    def query_tb_one(self, sql_query, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_query, query_tuple)
            result = self.cursor.fetchone()
        else:
            self.cursor.execute(sql_query)
            result = self.cursor.fetchone()
        return result

    def update_tb(self, sql_update, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_update, query_tuple)
            self.connect_db.commit()
        else:
            self.cursor.execute(sql_update)
            self.connect_db.commit()

    def delete_row(self, sql_delete):
        self.cursor.execute(sql_delete)
        self.connect_db.commit()

    def close_db(self):
        self.connect_db.close()

    def drop_tb(self, tb_name):
        sql_drop_tb = "DROP TABLE IF EXISTS {};".format(tb_name)
        self.cursor.execute(sql_drop_tb)
        self.connect_db.commit()

class DbWrapperMysqlDict:
    def __init__(self):
        self.connect_db = pymysql.connect(host=DBHOST,
                                    port=3306,
                                    user=DBUSER,
                                    password=DBPASSWORD,
                                    database=DBNAME,
                                    cursorclass=pymysql.cursors.DictCursor)

        self.cursor = self.connect_db.cursor()

    def query_tb_all(self, sql_query, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_query, query_tuple)
            result = self.cursor.fetchall()
        else:
            self.cursor.execute(sql_query)
            result = self.cursor.fetchall()
        return result

    def query_tb_one(self, sql_query, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_query, query_tuple)
            result = self.cursor.fetchone()
        else:
            self.cursor.execute(sql_query)
            result = self.cursor.fetchone()
        return result

    def update_tb(self, sql_update, query_tuple=None):
        if query_tuple:
            self.cursor.execute(sql_update, query_tuple)
            self.connect_db.commit()
        else:
            self.cursor.execute(sql_update)
            self.connect_db.commit()

    def close_db(self):
        self.connect_db.close()


class DbWrapperMysqlSqlalchemy:
    def __init__(self):
        engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                               .format(user=DBUSER,
                                       pw=DBPASSWORD,
                                       db=DBNAME,
                                       host=DBHOST))

        self.connection = engine.connect()

    def fetch_execute(self, sql):
        cursor = self.connection.execute(sql)
        return cursor











