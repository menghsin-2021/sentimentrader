from flask import Blueprint, Response, render_template, request, flash
from utils import get_cookie_check
from model import model_mongo
from datetime import datetime, timedelta
import json

# Blueprint
monitor = Blueprint('monitor', __name__, static_folder='static', template_folder='templates')


def get_day(days=0):
    yesterday_strftime = (datetime.today()-timedelta(days=days)).strftime('%Y-%m-%d')
    year = int(yesterday_strftime.split('-')[0])
    month = int(yesterday_strftime.split('-')[1])
    day = int(yesterday_strftime.split('-')[2])
    return year, month, day


def iso_date(days_before):
    year, month, day = get_day(days_before)
    if month < 10:
        month = "0" + str(month)
    if day < 10:
        day = "0" + str(day)
    try:
        create_time = datetime.fromisoformat(f'{year}-{month}-{day}')
    except:
        return None
    else:
        return create_time


def fetch_test_result(create_time_from, create_time_to, col_name):
    db_mongo = model_mongo.DbWrapperMongo()
    query_dict = {"create_time": {"$gte": create_time_from, "$lt": create_time_to}}
    print(query_dict)
    rows = db_mongo.find_sorted(col_name, query_dict, 'create_time', -1)
    rows = [row for row in rows]
    return rows


@monitor.route('/monitor.html', methods=['GET'])
def monitor_page():
    uid = get_cookie_check()
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')

    create_time_from = iso_date(8)
    create_time_to = iso_date(1)
    col_name = "stabilization"
    # col_name = "test"
    rows = fetch_test_result(create_time_from, create_time_to, col_name)
    print(rows)

    return render_template('monitor.html', rows=rows)

