import model_mysql
from datetime import datetime, timedelta

def get_today():
    today_strftime= datetime.today().strftime('%Y%m%d')
    week_strftime = datetime.today().strftime('%Y%u')
    month_strftime = datetime.today().strftime('%Y%m')
    year_strftime = datetime.today().strftime('%Y')

    return today_strftime, week_strftime, month_strftime, year_strftime

def get_day_before(i):
    days_ago_strftime = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') + ' 00:00:00'
    # 2021-11-05 00:00:00 (mysql date)
    return days_ago_strftime

today_strftime, week_strftime, month_strftime, year_strftime = get_today()
today = get_day_before(0)
weeks_ago_strftime = get_day_before(7)
month_ago_strftime = get_day_before(30)
year_ago_strftime = get_day_before(365)
three_year_ago_strftime = get_day_before(1095)
five_year_ago_strftime = get_day_before(1825)

print(three_year_ago_strftime)

sql_social_volume_daily = "CREATE TABLE `social_volume_daily_{}` AS \
                    SELECT DATE_FORMAT(date,'%Y%m%d') AS `days`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, `count`, `article_count` \
                    FROM `daily_social_volume` \
                    JOIN `stocks` \
                    ON daily_social_volume.stock_code = stocks.stock_code \
                    WHERE daily_social_volume.stock_code NOT IN (0, 1, 2, 3, 4, 5) \
                    AND `date` = '{}' \
                    AND `count` > 0 \
                    ORDER BY `days` DESC, `count` DESC, `article_count` DESC;".format(today_strftime, today)


sql_social_volume_weekly = "CREATE TABLE `social_volume_weekly_{}` AS \
                            SELECT DATE_FORMAT(date,'%Y%u') AS `weeks`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) AS `count`, sum(article_count) AS `article_count` \
                            FROM sentimentrader.daily_social_volume \
                            JOIN stocks \
                            ON daily_social_volume.stock_code = stocks.stock_code \
                            WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                            AND `date` > '{}' \
                            GROUP BY `source`, `weeks`, `stock_code`\
                            HAVING count > 0 \
                            ORDER BY `count` desc, `article_count` desc;".format(today_strftime, weeks_ago_strftime)


sql_social_volume_monthly = "CREATE TABLE `social_volume_monthly_{}` AS \
                            SELECT DATE_FORMAT(date,'%Y%m') AS `months`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) AS `count`, sum(article_count) AS `article_count` \
                            FROM sentimentrader.daily_social_volume \
                            JOIN stocks \
                            ON daily_social_volume.stock_code = stocks.stock_code \
                            WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                            AND `date` > '{}' \
                            GROUP BY `source`, `months`, `stock_code`\
                            HAVING count > 0 \
                            ORDER BY `count` desc, `article_count` desc;".format(today_strftime, month_ago_strftime)


sql_social_volume_yearly = "CREATE TABLE `social_volume_yearly_{}` AS \
                            SELECT DATE_FORMAT(date,'%Y') as `years`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) as `count`, sum(article_count) as `article_count` \
                            FROM sentimentrader.daily_social_volume \
                            JOIN stocks \
                            ON daily_social_volume.stock_code = stocks.stock_code \
                            WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                            AND `date` > '{}' \
                            GROUP BY `source`, `years`, `stock_code`\
                            HAVING count > 0 \
                            ORDER BY `count` desc, `article_count` desc;".format(today_strftime, year_ago_strftime)

sql_social_volume_three_yearly = "CREATE TABLE `social_volume_three_yearly_{}` AS \
                                SELECT DATE_FORMAT(date,'%Y') as `years`, `source`, `category`, daily_social_volume.stock_code, `stock_name`, sum(count) as `count`, sum(article_count) as `article_count` \
                                FROM sentimentrader.daily_social_volume \
                                JOIN stocks \
                                ON daily_social_volume.stock_code = stocks.stock_code \
                                WHERE daily_social_volume.stock_code not in (0, 1, 2, 3, 4, 5) \
                                AND `date` > '{}' \
                                GROUP BY `source`, `years`, `stock_code`\
                                HAVING count > 0 \
                                ORDER BY `count` desc, `article_count` desc;".format(today_strftime, three_year_ago_strftime)



sql_sentiment_daily = "CREATE TABLE `sentiment_daily_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code, `stock_name`, `category`, \
        	           `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                       FROM `sentimentrader`.`daily_sentiment` \
                       JOIN stocks \
                       ON daily_sentiment.stock_code = stocks.stock_code \
                       order by `days` desc;".format(today_strftime)


sql_sentiment_weekly = "CREATE TABLE `sentiment_weekly_{}` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code as `stock_code`, `stock_name`, `category`, \
    	                `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                       FROM `sentimentrader`.`daily_sentiment` \
                        JOIN stocks \
                        ON daily_sentiment.stock_code = stocks.stock_code \
                        WHERE `date` > '{}' \
                        order by `days` desc;".format(today_strftime, weeks_ago_strftime)

sql_sentiment_monthly = "CREATE TABLE `sentiment_monthly_{}` AS \
                         SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code as `stock_code`, `stock_name`, `category`, \
    	                 `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                         FROM `sentimentrader`.`daily_sentiment` \
                         JOIN stocks \
                         ON daily_sentiment.stock_code = stocks.stock_code \
                         WHERE `date` > '{}' \
                         order by `days` desc;".format(today_strftime, month_ago_strftime)

sql_sentiment_yearly = "CREATE TABLE `sentiment_yearly_{}` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code as `stock_code`, `stock_name`, `category`, \
    	                `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                        FROM `sentimentrader`.`daily_sentiment` \
                        JOIN stocks \
                        ON daily_sentiment.stock_code = stocks.stock_code \
                        WHERE `date` > '{}' \
                        order by `days` desc;".format(today_strftime, year_ago_strftime)

sql_sentiment_three_yearly = "CREATE TABLE `sentiment_three_yearly_{}` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code as `stock_code`, `stock_name`, `category`, \
    	                `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                        FROM `sentimentrader`.`daily_sentiment` \
                        JOIN stocks \
                        ON daily_sentiment.stock_code = stocks.stock_code \
                        WHERE `date` > '{}' \
                        order by `days` desc;".format(today_strftime, three_year_ago_strftime)

sql_sentiment_five_yearly = "CREATE TABLE `sentiment_five_yearly_{}` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, `source`, daily_sentiment.stock_code as `stock_code`, `stock_name`, `category`, \
    	                `sum_valence`, (`avg_valence` - 5) as `avg_valence`, `sum_arousal`, (`avg_arousal` - 5 ) as `avg_arousal`, `sum_sentiment` \
                        FROM `sentimentrader`.`daily_sentiment` \
                        JOIN stocks \
                        ON daily_sentiment.stock_code = stocks.stock_code \
                        WHERE `date` > '{}' \
                        order by `days` desc;".format(today_strftime, five_year_ago_strftime)

sql_stock_price_daily = "CREATE TABLE `stock_price_daily_{}` AS \
                        SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                        FROM `sentimentrader`.`daily_stock_price` \
                        JOIN `stocks` \
                        ON daily_stock_price.stock_code = `stocks`.`stock_code` \
                        WHERE `date` > '2013-01-01 00:00:00' \
                        ORDER BY `days` desc;".format(today_strftime)


sql_stock_price_weekly = "CREATE TABLE `stock_price_weekly_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code as `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `sentimentrader`.`daily_stock_price` \
                       JOIN `stocks` \
                       ON daily_stock_price.stock_code = stocks.stock_code \
                       WHERE `date` > '{}' \
                       ORDER BY `days` desc;".format(today_strftime, weeks_ago_strftime)

sql_stock_price_monthly = "CREATE TABLE `stock_price_monthly_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code as `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `sentimentrader`.`daily_stock_price` \
                       JOIN `stocks` \
                       ON daily_stock_price.stock_code = stocks.stock_code \
                       WHERE `date` > '{}' \
                       ORDER BY `days` desc;".format(today_strftime, month_ago_strftime)

sql_stock_price_yearly = "CREATE TABLE `stock_price_yearly_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code as `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `sentimentrader`.`daily_stock_price` \
                       JOIN `stocks` \
                       ON daily_stock_price.stock_code = stocks.stock_code \
                       WHERE `date` > '{}' \
                       ORDER BY `days` desc;".format(today_strftime, year_ago_strftime)

sql_stock_price_three_yearly = "CREATE TABLE `stock_price_three_yearly_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code as `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `sentimentrader`.`daily_stock_price` \
                       JOIN `stocks` \
                       ON daily_stock_price.stock_code = stocks.stock_code \
                       WHERE `date` > '{}' \
                       ORDER BY `days` desc;".format(today_strftime, three_year_ago_strftime)

sql_stock_price_five_yearly = "CREATE TABLE `stock_price_five_yearly_{}` AS \
                       SELECT DATE_FORMAT(date, '%Y-%m-%d') as `days`, daily_stock_price.stock_code as `stock_code`, `stock_name`, `category`, `open`, `low`, `high`, `close`, `volume` \
                       FROM `sentimentrader`.`daily_stock_price` \
                       JOIN `stocks` \
                       ON daily_stock_price.stock_code = stocks.stock_code \
                       WHERE `date` > '{}' \
                       ORDER BY `days` desc;".format(today_strftime, five_year_ago_strftime)



db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
db_mysql.cursor.execute(sql_social_volume_daily)
db_mysql.cursor.execute(sql_social_volume_weekly)
db_mysql.cursor.execute(sql_social_volume_monthly)
db_mysql.cursor.execute(sql_social_volume_yearly)
db_mysql.cursor.execute(sql_social_volume_three_yearly)


db_mysql.cursor.execute(sql_sentiment_daily)
db_mysql.cursor.execute(sql_sentiment_weekly)
db_mysql.cursor.execute(sql_sentiment_monthly)
db_mysql.cursor.execute(sql_sentiment_yearly)
db_mysql.cursor.execute(sql_sentiment_three_yearly)
db_mysql.cursor.execute(sql_sentiment_five_yearly)

db_mysql.cursor.execute(sql_stock_price_daily)
db_mysql.cursor.execute(sql_stock_price_weekly)
db_mysql.cursor.execute(sql_stock_price_monthly)
db_mysql.cursor.execute(sql_stock_price_yearly)
db_mysql.cursor.execute(sql_stock_price_three_yearly)
db_mysql.cursor.execute(sql_stock_price_five_yearly)