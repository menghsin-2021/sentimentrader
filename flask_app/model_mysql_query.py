# social_volume
sql_social_volume = "SELECT *, (`count` + `article_count`) as total \
                         FROM `social_volume_daily` \
                         WHERE `source` = 'ptt' \
                         ORDER BY `total` DESC \
                         limit 10;"

# sentiment
sql_stock_price = "SELECT `days`, `open`, `low`, `high`, `close`, `volume` \
                           FROM `stock_price_view` \
                           WHERE stock_code = %s \
                           ORDER BY `days` desc;"

sql_sentiment = "SELECT `days`, `stock_name`, `sum_valence`, `avg_valence`, `sum_arousal`, `avg_arousal`, `sum_sentiment` \
                             FROM `sentiment_view` \
                             WHERE `source` = '%s' \
                             AND `stock_code` = '%s' \
                             ORDER BY `days` desc;"

sql_social_volume_electric_car = "SELECT `stock_name`, `stock_code`, `count`, `article_count`, (`count` + `article_count`) as total \
                         FROM `social_volume_daily` \
                         WHERE `source` = '{}' \
                         AND `category` = '{}' \
                         OR `category` = '{}' \
                         ORDER BY `total` DESC \
                         limit 10;".format(source, category, category_1)