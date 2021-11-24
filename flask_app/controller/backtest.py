from flask import Blueprint, render_template, request, flash, redirect, url_for
import json

import config
from model import model_mysql
from model import model_mysql_query
from utils import get_cookie_check, delete_file, GetName


# Blueprint
backtest = Blueprint('backtest', __name__, static_folder='static', template_folder='templates')

BUCKET_NAME = config.BUCKET_NAME
OBJECT_PATH = config.OBJECT_PATH

get_name = GetName()

@backtest.route('/backtest.html', methods=['GET'])
def backtest_page():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')

    try:
        db_mysql = model_mysql.DbWrapperMysqlDict('sentimentrader')
        sql_backtest = model_mysql_query.sql_backtest
        strategy_backtest_dict_list = db_mysql.query_tb_all(sql_backtest, (uid,))
        strategy_backtest_dict_list_length = int(len(strategy_backtest_dict_list))
        return render_template('backtest.html', strategy_backtest_dict_list=strategy_backtest_dict_list, strategy_backtest_dict_list_length=strategy_backtest_dict_list_length)

    except:
        flash('請先建立策略做回測', 'info')
        return redirect(url_for('strategy.strategy_page'))


@backtest.route('/api/1.0/send_backtest', methods=['POST'])
def send_backtest():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')
    else:
        send_backtest_strategy_id = request.form.to_dict()['send_backtest']
        print(send_backtest_strategy_id)
        db_mysql = model_mysql.DbWrapperMysqlDict('sentimentrader')
        sql_fetch_strategy_backtest = model_mysql_query.sql_fetch_strategy_backtest
        send_backtest = db_mysql.query_tb_one(sql_fetch_strategy_backtest, (send_backtest_strategy_id,))
        print(send_backtest)

        send_backtest['category_name'] = get_name.category(send_backtest['category'])
        send_backtest['strategy_line_name'] = get_name.strategy_line(send_backtest['strategy_line'])
        send_backtest['strategy_in_name'] = get_name.strategy_in(send_backtest['strategy_in'])
        send_backtest['strategy_out_name'] = get_name.strategy_out(send_backtest['strategy_out'])
        send_backtest['strategy_sentiment_name'] = get_name.strategy_sentiment(send_backtest['strategy_sentiment'])
        send_backtest['source_name'] = get_name.source(send_backtest['source'])

        db_mysql = model_mysql.DbWrapperMysqlDict('sentimentrader')
        sql_sample_strategy = model_mysql_query.sql_sample_strategy
        sample_strategy_form = db_mysql.query_tb_all(sql_sample_strategy)
        sample_strategy_form_length = int(len(sample_strategy_form))

        def add_key(sample_strategy):
            sample_strategy['category_name'] = get_name.category(sample_strategy['category'])
            sample_strategy['strategy_line_name'] = get_name.strategy_line(sample_strategy['strategy_line'])
            sample_strategy['strategy_in_name'] = get_name.strategy_in(sample_strategy['strategy_in'])
            sample_strategy['strategy_out_name'] = get_name.strategy_out(sample_strategy['strategy_out'])
            sample_strategy['strategy_sentiment_name'] = get_name.strategy_sentiment(sample_strategy['strategy_sentiment'])
            sample_strategy['source_name'] = get_name.source(sample_strategy['source'])
            return sample_strategy

        sample_strategy_form = [add_key(sample_strategy) for sample_strategy in sample_strategy_form]

        return render_template('strategy.html', send_backtest=send_backtest, sample_strategy_form=sample_strategy_form, sample_strategy_form_length=sample_strategy_form_length)


@backtest.route('/api/1.0/remove_strategy', methods=['POST'])
def remove_strategy():
    form = json.loads(list(request.form.keys())[0])
    strategy_id = form['strategy_id']
    file_path = form['file_path']
    user_id = form['user_id']

    sql_delete_strategy = "DELETE FROM `strategy_backtest` WHERE `id` = '{}'".format(strategy_id)
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    db_mysql.delete_row(sql_delete_strategy)
    print(f"strategy {strategy_id} is deleted")

    file_name = file_path.split("/")[-1]
    delete_file(BUCKET_NAME, OBJECT_PATH, user_id, file_name)

    return redirect(url_for('backtest.backtest_page'))
