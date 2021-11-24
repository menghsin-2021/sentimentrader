from flask import Blueprint, Response, render_template, request, flash
from utils import get_cookie_check
import model_mysql
import model_mysql_query
import json



# Blueprint
social_volume = Blueprint('social_volume', __name__, static_folder='static', template_folder='templates')


@social_volume.route('/social_volume.html', methods=['GET'])
def social_volume_page():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')
    # user count
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    sql_social_volume = model_mysql_query.sql_social_volume
    result = db_mysql.query_tb_all(sql_social_volume)

    stock_name_code = [f'{word_count[4]}, {word_count[3]}' for word_count in result]
    stock_count = [int(word_count[5]) for word_count in result]
    article_count = [int(word_count[6]) for word_count in result]
    social_volume_rank = json.dumps({
        'stock_name_code': stock_name_code,
        'stock_count': stock_count,
        'article_count': article_count,
        'title': '個股媒體熱度排名(當日)',
        'category': "",
        'category_name': '所有類別',
        'duration': "daily",
        'duration_name': '當日',
        'source': 'ptt',
        'source_name': 'PTT 論壇',
    }, indent=2, ensure_ascii=False)
    print(social_volume_rank)
    return render_template('social_volume.html', social_volume_rank=social_volume_rank)


@social_volume.route('/api/1.0/social_volume_rank', methods=['POST'])
def social_volume_rank():
    form = request.form.to_dict()
    category = form['category']
    duration = form['duration']
    source = form['source']

    if duration == 'day':
        if category == 'electric' or category == 'electric_car':
            category_1 = 'electric_electric_car'
            sql_social_volume = "SELECT `stock_name`, `stock_code`, `count`, `article_count`, (`count` + `article_count`) as total \
                                     FROM `social_volume_daily` \
                                     WHERE `source` = '{}' \
                                     AND `category` = '{}' \
                                     OR `category` = '{}' \
                                     ORDER BY `total` DESC \
                                     limit 10;".format(source, category, category_1)
        else:
            sql_social_volume = "SELECT `stock_name`, `stock_code`, `count`, `article_count`, (`count` + `article_count`) as total \
                                 FROM `social_volume_daily` \
                                 WHERE `source` = '{}' \
                                 AND `category` = '{}' \
                                 ORDER BY `total` DESC \
                                 limit 10;".format(source, category)

    else:
        if category == 'electric' or category == 'electric_car':
            category_1 = 'electric_electric_car'
            sql_social_volume = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                         FROM `social_volume_{}` \
                                         WHERE `source` = '{}' \
                                         AND `category` = '{}' \
                                         OR `category` = '{}' \
                                         GROUP BY `stock_code` \
                                         ORDER BY `total` DESC \
                                         limit 10;".format(duration, source, category, category_1)
        else:
            sql_social_volume = "SELECT `stock_name`, `stock_code`, SUM(`count`) as `count`, SUM(`article_count`) AS `article_count`, (SUM(`count`) +  SUM(`article_count`)) as total \
                                 FROM `social_volume_{}` \
                                 WHERE `source` = '{}' \
                                 AND `category` = '{}' \
                                 GROUP BY `stock_code` \
                                 ORDER BY `total` DESC \
                                 limit 10;".format(duration, source, category)
    category_name_dict = {
        "electric_car": "電動車",
        "electric": "電子資訊",
        "sail": "航運",
        "biotech": "生技",
        "finance": "金融",
    }

    source_name_dict = {
        "ptt": "PTT 貼文",
        "cnyes": "鉅亨網"
    }

    duration_name_dict = {
        "daily": "當日",
        "weekly": "當周",
        "monthly": "當月",
        "yearly": "一年內",
        "three_yearly": "三年內"
    }
    category_name = category_name_dict[category]
    source_name = source_name_dict[source]
    duration_name = duration_name_dict[duration]

    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    result = db_mysql.query_tb_all(sql_social_volume)
    print(result)
    stock_name_code = [f'{word_count[0]}, {word_count[1]}' for word_count in result]
    stock_count = [int(word_count[2]) for word_count in result]
    article_count = [int(word_count[3]) for word_count in result]
    social_volume_rank = json.dumps({
        'stock_name_code': stock_name_code,
        'stock_count': stock_count,
        'article_count': article_count,
        'title': f"{category_name}, {duration_name}, {source_name} 個股媒體熱度排名",
        'category': category,
        'category_name': category_name,
        'duration': duration,
        'duration_name': duration_name,
        'source': source,
        'source_name': source_name,
    }, indent=2, ensure_ascii=False)
    print(social_volume_rank)

    if len(stock_name_code) == 0:
        flash('本日於該媒體還未有此類股相關提及', 'info')
        return render_template('social_volume.html', social_volume_rank=social_volume_rank)
    else:
        return render_template('social_volume.html', social_volume_rank=social_volume_rank)
