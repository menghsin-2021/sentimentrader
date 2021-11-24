import model_mysql
from datetime import datetime, timedelta

def get_today():
    today_strftime= datetime.today().strftime('%Y%m%d')
    yesterday_strftime = (datetime.today() - timedelta(days=1)).strftime('%Y%m%d')
    # week_strftime = datetime.today().strftime('%Y%u')
    # month_strftime = datetime.today().strftime('%Y%m')
    # year_strftime = datetime.today().strftime('%Y')

    return today_strftime, yesterday_strftime

def get_day_before(i):
    days_ago_strftime = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') + ' 00:00:00'
    # 2021-11-05 00:00:00 (mysql date)
    return days_ago_strftime

today_strftime, yesterday_strftime = get_today()
today = get_day_before(0)
yesterday = get_day_before(1)
weeks_ago_strftime = get_day_before(7)
month_ago_strftime = get_day_before(30)
year_ago_strftime = get_day_before(365)
three_year_ago_strftime = get_day_before(1095)
five_year_ago_strftime = get_day_before(1825)


sql_drop_social_volume_view = "DROP TABLE IF EXISTS `social_volume_view`;"

sql_social_volume_daily = "CREATE TABLE `social_volume_daily` AS \
                           SELECT DATE_FORMAT(date,'%Y%m%d') AS `days`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, `count`, `article_count` \
                           FROM `daily_social_volume` \
                           JOIN `stocks` \
                           ON daily_social_volume.stock_code = stocks.stock_code \
                           WHERE daily_social_volume.stock_code NOT IN (0, 1, 2, 3, 4, 5) \
                           AND `date` = '{}' \
                           AND `count` > 0 \
                           ORDER BY `days` DESC, `count` DESC, `article_count` DESC;".format(today)

sql_social_volume_weekly = "CREATE TABLE `social_volume_weekly` AS \
                            SELECT DATE_FORMAT(date,'%Y%u') AS `weeks`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) AS `count`, sum(article_count) AS `article_count` \
                            FROM sentimentrader.daily_social_volume \
                            JOIN stocks \
                            ON daily_social_volume.stock_code = stocks.stock_code \
                            WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                            AND `date` > '{}' \
                            GROUP BY `source`, `weeks`, `stock_code`\
                            HAVING count > 0 \
                            ORDER BY `count` desc, `article_count` desc;".format(weeks_ago_strftime)

sql_social_volume_monthly = "CREATE TABLE `social_volume_monthly` AS \
                             SELECT DATE_FORMAT(date,'%Y%m') AS `months`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) AS `count`, sum(article_count) AS `article_count` \
                             FROM sentimentrader.daily_social_volume \
                             JOIN stocks \
                             ON daily_social_volume.stock_code = stocks.stock_code \
                             WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                             AND `date` > '{}' \
                             GROUP BY `source`, `months`, `stock_code`\
                             HAVING count > 0 \
                             ORDER BY `count` desc, `article_count` desc;".format(month_ago_strftime)

sql_social_volume_yearly = "CREATE TABLE `social_volume_yearly` AS \
                            SELECT DATE_FORMAT(date,'%Y') as `years`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) as `count`, sum(article_count) as `article_count` \
                            FROM sentimentrader.daily_social_volume \
                            JOIN stocks \
                            ON daily_social_volume.stock_code = stocks.stock_code \
                            WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                            AND `date` > '{}' \
                            GROUP BY `source`, `years`, `stock_code`\
                            HAVING count > 0 \
                            ORDER BY `count` desc, `article_count` desc;".format(year_ago_strftime)

sql_social_volume_three_yearly = "CREATE TABLE `social_volume_three_yearly` AS \
                                  SELECT DATE_FORMAT(date,'%Y') as `years`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) as `count`, sum(article_count) as `article_count` \
                                  FROM sentimentrader.daily_social_volume \
                                  JOIN stocks \
                                  ON daily_social_volume.stock_code = stocks.stock_code \
                                  WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                                  AND `date` > '{}' \
                                  GROUP BY `source`, `years`, `stock_code`\
                                  HAVING count > 0 \
                                  ORDER BY `count` desc, `article_count` desc;".format(three_year_ago_strftime)

sql_social_volume_union = "CREATE TABLE `social_volume_view` AS \
                           SELECT `days` as `date`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, 'daily' as `duration` FROM `social_volume_daily` \
                           UNION \
                           SELECT `weeks` as `date`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, 'weekly' as `duration` FROM `social_volume_weekly` \
                           UNION \
                           SELECT `months` as  `date`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, 'monthly' as `duration` FROM `social_volume_monthly` \
                           UNION \
                           SELECT `years` as `date`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, 'yearly' as `duration` FROM `social_volume_yearly` \
                           UNION \
                           SELECT `years` as  `date`, `source`, `category`, `stock_code`, `stock_name`, `count`, `article_count`, 'three_yearly' as `duration` FROM `social_volume_three_yearly`;"


sql_social_volume_union_set_index_category = "ALTER TABLE sentimentrader.social_volume_view ADD INDEX (`category`);"
sql_social_volume_union_set_index_duration = "ALTER TABLE sentimentrader.social_volume_view ADD INDEX (`duration`);"

sql_drop_social_volume_daily = "DROP TABLE IF EXISTS social_volume_daily;"
sql_drop_social_volume_weekly = "DROP TABLE IF EXISTS social_volume_weekly;"
sql_drop_social_volume_monthly = "DROP TABLE IF EXISTS social_volume_monthly;"
sql_drop_social_volume_yearly = "DROP TABLE IF EXISTS social_volume_yearly;"
sql_drop_social_volume_three_yearly = "DROP TABLE IF EXISTS social_volume_three_yearly;"


# sentiment
sql_drop_sentiment_view = "DROP TABLE IF EXISTS sentiment_view;"

sql_sentiment_view = "CREATE TABLE `sentiment_view` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code, `stock_name`, `category`, \
        	           `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                       FROM `sentimentrader`.`daily_sentiment` \
                       JOIN stocks \
                       ON daily_sentiment.stock_code = stocks.stock_code \
                       order by `days` desc;"

sql_sentiment_view_set_index = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`days`);"
sql_sentiment_view_set_index_source = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`source`);"
sql_sentiment_view_set_index_stock_code = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`stock_code`);"
sql_sentiment_view_set_index_stock_name = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`stock_name`);"
sql_sentiment_view_set_index_category = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`category`);"
sql_sentiment_view_set_index_source_stock_code = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`source`, `stock_code`);"
sql_sentiment_view_set_index_day_source_stock_code = "ALTER TABLE sentimentrader.sentiment_view ADD INDEX (`days`, `source`, `stock_code`);"


# stock price
sql_drop_stock_price_view = "DROP TABLE IF EXISTS `stock_price_view`;"


sql_stock_price_daily = "CREATE TABLE `stock_price_view` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                        FROM `sentimentrader`.`daily_stock_price` \
                        JOIN `stocks` \
                        ON daily_stock_price.stock_code = `stocks`.`stock_code` \
                        ORDER BY `days` desc;"

sql_stock_price_view_set_index = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`days`);"
sql_stock_price_view_set_index_stock_code = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`stock_code`);"
sql_stock_price_view_set_index_stock_name = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`stock_name`);"
sql_stock_price_view_set_index_category = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`category`);"
sql_stock_price_view_set_index_source_stock_code = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`category`, `stock_code`);"
sql_stock_price_view_set_index_day_source_stock_code = "ALTER TABLE sentimentrader.stock_price_view ADD INDEX (`days`, `category`, `stock_code`);"




db_mysql = model_mysql.DbWrapperMysql('sentimentrader')

try:
    db_mysql.cursor.execute(sql_drop_social_volume_view)
except:
    pass
try:
    db_mysql.cursor.execute(sql_drop_sentiment_view)
except:
    pass
try:
    db_mysql.cursor.execute(sql_drop_stock_price_view)
except:
    pass

db_mysql.cursor.execute(sql_social_volume_daily)
db_mysql.cursor.execute(sql_social_volume_weekly)
db_mysql.cursor.execute(sql_social_volume_monthly)
db_mysql.cursor.execute(sql_social_volume_yearly)
db_mysql.cursor.execute(sql_social_volume_three_yearly)
db_mysql.cursor.execute(sql_social_volume_union)

db_mysql.cursor.execute(sql_social_volume_union_set_index_category)
db_mysql.cursor.execute(sql_social_volume_union_set_index_duration)

db_mysql.cursor.execute(sql_drop_social_volume_daily)
db_mysql.cursor.execute(sql_drop_social_volume_weekly)
db_mysql.cursor.execute(sql_drop_social_volume_monthly)
db_mysql.cursor.execute(sql_drop_social_volume_yearly)
db_mysql.cursor.execute(sql_drop_social_volume_three_yearly)

db_mysql.cursor.execute(sql_sentiment_view)
db_mysql.cursor.execute(sql_sentiment_view_set_index)
db_mysql.cursor.execute(sql_sentiment_view_set_index_source)
db_mysql.cursor.execute(sql_sentiment_view_set_index_stock_code)
db_mysql.cursor.execute(sql_sentiment_view_set_index_stock_name)
db_mysql.cursor.execute(sql_sentiment_view_set_index_category)
db_mysql.cursor.execute(sql_sentiment_view_set_index_source_stock_code)
db_mysql.cursor.execute(sql_sentiment_view_set_index_day_source_stock_code)

db_mysql.cursor.execute(sql_stock_price_daily)
db_mysql.cursor.execute(sql_stock_price_view_set_index)
db_mysql.cursor.execute(sql_stock_price_view_set_index_stock_code)
db_mysql.cursor.execute(sql_stock_price_view_set_index_stock_name)
db_mysql.cursor.execute(sql_stock_price_view_set_index_category)
db_mysql.cursor.execute(sql_stock_price_view_set_index_source_stock_code)
db_mysql.cursor.execute(sql_stock_price_view_set_index_day_source_stock_code)

db_mysql.close_db()