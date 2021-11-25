from flask import Blueprint, Response, render_template, request, flash
from utils import get_cookie_check, SocialVolumeFetch, GetName
import json


# Blueprint
social_volume = Blueprint('social_volume', __name__, static_folder='static', template_folder='templates')


@social_volume.route('/social_volume.html', methods=['GET'])
def social_volume_page():
    uid = get_cookie_check()
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')

    # fetch social volume all
    social_volume_fetch = SocialVolumeFetch()
    stock_name_code, stock_count, article_count = social_volume_fetch.fetch_social_volume()

    # create json
    social_volume_rank = json.dumps({
        'stock_name_code': stock_name_code,
        'stock_count': stock_count,
        'article_count': article_count,
        'title': '所有個股媒體熱度排名(當日)',
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
    uid = get_cookie_check()
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')

    # get form
    form = request.form.to_dict()
    category = form['category']
    duration = form['duration']
    source = form['source']

    # fetch social volume category
    social_volume_fetch = SocialVolumeFetch()
    stock_name_code, stock_count, article_count = social_volume_fetch.fetch_social_volume(category, source, duration)

    # change code to name
    get_name = GetName()
    category_name = get_name.category(category)
    source_name = get_name.source(source)
    duration_name = get_name.duration(duration)

    # create json
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
