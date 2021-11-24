# social_volume
sql_social_volume = "SELECT *, (`count` + `article_count`) as total \
                     FROM `social_volume_view` \
                     WHERE `source` = 'ptt' \
                     AND `duration` = 'daily' \
                     ORDER BY `total` DESC \
                     limit 10;"


sql_social_volume_duration_electric = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                       FROM `social_volume_view` \
                                       WHERE `source` = %s \
                                       AND `duration` = %s \
                                       AND `category` = %s \
                                       OR `category` = %s \
                                       GROUP BY `stock_code` \
                                       ORDER BY `total` DESC \
                                       limit 10;"

sql_social_volume_duration_another_category = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                                FROM `social_volume_view` \
                                                WHERE `source` = %s \
                                                AND `duration` = %s \
                                                AND `category` = %s \
                                                GROUP BY `stock_code` \
                                                ORDER BY `total` DESC \
                                                limit 10;"

# sentiment
sql_stock_price = "SELECT `days`, `open`, `low`, `high`, `close`, `volume` \
                   FROM `stock_price_view` \
                   WHERE stock_code = %s \
                   ORDER BY `days` desc;"

sql_sentiment = "SELECT `days`, `stock_name`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment` \
                 FROM `sentiment_view` \
                 WHERE `source` = %s \
                 AND `stock_code` = %s \
                 ORDER BY `days` desc;"


# strategy
sql_sample_strategy = "SELECT * \
                       FROM `strategy_backtest` \
                       JOIN `stocks` \
                       ON `strategy_backtest`.`stock_code` = `stocks`.`stock_code` \
                       WHERE `user_id` = '20' \
                       ORDER BY `create_date` DESC, `id` DESC \
                       limit 15;"

def sql_strategy_stock_price(stock_code, start_date_datetime, end_date_datetime):
    return "SELECT DATE_FORMAT(date,'%%Y-%%m-%%d') AS Date, open AS Open, high AS High, \
            low AS Low, close AS Close, volume AS Volume \
            FROM sentimentrader.daily_stock_price \
            WHERE stock_code = '{}' \
            AND `date` BETWEEN '{}' and '{}' \
            ORDER BY `Date`".format(stock_code, start_date_datetime, end_date_datetime)


def sql_strategy_sentiment(source, stock_code, start_date_datetime, end_date_datetime):
    return "SELECT DATE_FORMAT(date,'%%Y-%%m-%%d') AS Date, (avg_valence - 5) as avg_valence, (avg_arousal - 5) as avg_arousal, sum_sentiment \
            FROM sentimentrader.daily_sentiment \
            WHERE source = '{}' \
            AND stock_code = '{}' \
            AND `date` BETWEEN '{}' and '{}' \
            ORDER BY `Date`".format(source, stock_code, start_date_datetime, end_date_datetime)
