from flask import Blueprint, render_template, request, flash, redirect, url_for
import json

import config
import model_mysql
from utils import get_cookie_check, delete_file


# Blueprint
backtest = Blueprint('backtest', __name__, static_folder='static', template_folder='templates')

BUCKET_NAME = config.BUCKET_NAME
OBJECT_PATH = config.OBJECT_PATH


@backtest.route('/backtest.html', methods=['GET'])
def backtest_page():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')
    else:
        sql_backtest = "SELECT * \
                             FROM `strategy_backtest` \
                             JOIN `stocks` \
                             ON `strategy_backtest`.`stock_code` = `stocks`.`stock_code` \
                             WHERE `user_id` = '{}' \
                             ORDER BY `create_date` DESC, `id` DESC \
                             limit 15;".format(uid)

        try:
            db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
            result = db_mysql.query_tb_all(sql_backtest)
            # pprint(result[0])
            strategy_backtest_dict_list = [{
                    'strategy_id': strategy_backtest[0],
                    'user_id': strategy_backtest[1],
                    'stock_code': strategy_backtest[2],
                    'start_date': strategy_backtest[3],
                    'end_date': strategy_backtest[4],
                    'strategy_line': strategy_backtest[5],
                    'strategy_in': strategy_backtest[6],
                    'strategy_in_para': strategy_backtest[7],
                    'strategy_out': strategy_backtest[8],
                    'strategy_out_para': strategy_backtest[9],
                    'strategy_sentiment': strategy_backtest[10],
                    'source': strategy_backtest[11],
                    'sentiment_para_more': strategy_backtest[12],
                    'sentiment_para_less': strategy_backtest[13],
                    'seed_money': strategy_backtest[14],
                    'discount': strategy_backtest[15],
                    'total_buy_count': strategy_backtest[16],
                    'total_sell_count': strategy_backtest[17],
                    'total_return_rate': strategy_backtest[18],
                    'highest_return': strategy_backtest[19],
                    'lowest_return': strategy_backtest[20],
                    'total_win': strategy_backtest[21],
                    'total_lose': strategy_backtest[22],
                    'total_trade': strategy_backtest[23],
                    'win_rate': strategy_backtest[24],
                    'avg_return_rate': strategy_backtest[25],
                    'irr': strategy_backtest[26],
                    'file_path': strategy_backtest[27],
                    'create_date': strategy_backtest[28],
                    'stock_name': strategy_backtest[30]
                } for strategy_backtest in result]

            strategy_backtest_dict_list_length = int(len(strategy_backtest_dict_list))
            # pprint(strategy_backtest_dict_list[0])
            print(strategy_backtest_dict_list_length)
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

        sql_fetch_category = "SELECT * \
                              FROM `strategy_backtest` \
                              JOIN `stocks` \
                              ON `strategy_backtest`.`stock_code` = `stocks`.`stock_code` \
                              WHERE `id` = '{}';".format(send_backtest_strategy_id)

        # sql_fetch_category = "SELECT `category`, `stock_name` \
        #                      FROM `stocks` \
        #                      WHERE `stock_code` = '{}';".format(send_backtest['stock_code'])

        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        strategy_backtest = db_mysql.query_tb_one(sql_fetch_category)
        print(strategy_backtest)

        send_backtest = {
                'strategy_id': strategy_backtest[0],
                'user_id': strategy_backtest[1],
                'stock_code': strategy_backtest[2],
                'start_date': strategy_backtest[3],
                'end_date': strategy_backtest[4],
                'strategy_line': strategy_backtest[5],
                'strategy_in': strategy_backtest[6],
                'strategy_in_para': strategy_backtest[7],
                'strategy_out': strategy_backtest[8],
                'strategy_out_para': strategy_backtest[9],
                'strategy_sentiment': strategy_backtest[10],
                'source': strategy_backtest[11],
                'sentiment_para_more': strategy_backtest[12],
                'sentiment_para_less': strategy_backtest[13],
                'seed_money': strategy_backtest[14],
                'discount': strategy_backtest[15],
                'total_buy_count': strategy_backtest[16],
                'total_sell_count': strategy_backtest[17],
                'total_return_rate': strategy_backtest[18],
                'highest_return': strategy_backtest[19],
                'lowest_return': strategy_backtest[20],
                'total_win': strategy_backtest[21],
                'total_lose': strategy_backtest[22],
                'total_trade': strategy_backtest[23],
                'win_rate': strategy_backtest[24],
                'avg_return_rate': strategy_backtest[25],
                'irr': strategy_backtest[26],
                'file_path': strategy_backtest[27],
                'create_date': strategy_backtest[28],
            'stock_name': strategy_backtest[30],
            'category': strategy_backtest[31]
            }


        category_name = {
            "electric_electric_car": "電動車",
            "electric_car": "電動車",
            "electric": "電子資訊",
            "sail": "航運",
            "biotech": "生技",
            "finance": "金融",
            "stock_market": "台積電",
        }

        strategy_line_name = {
            "none": "--",
            "undefined": "--",
            "kdj_line": "ＫＤ線交叉",
            "macd_line": "ＭＡＣＤ線交叉",
            "none_line": "自訂",
        }

        strategy_in_name = {
            "none": "--",
            "increase_in": "股價連續上漲(3日)",
            "decrease_in": "股價連續下跌(3日)"
        }

        strategy_out_name = {
            "none": "--",
            "increase_out": "股價連續上漲(3日)",
            "decrease_out": "股價連續下跌(3日)"
        }

        strategy_sentiment_name = {
            "none_pass": "--",
            "daily_sentiment_pass": "當日情緒分數",
            "to_negative_pass": "正轉負",
            "to_positive_pass": "負轉正",
        }

        source_name = {
            "ptt": "PTT 論壇",
            "cnyes": "鉅亨網新聞",
        }

        send_backtest['category_name'] = category_name[send_backtest['category']]
        send_backtest['strategy_line_name'] = strategy_line_name[send_backtest['strategy_line']]
        send_backtest['strategy_in_name'] = strategy_in_name[send_backtest['strategy_in']]
        send_backtest['strategy_out_name'] = strategy_out_name[send_backtest['strategy_out']]
        send_backtest['strategy_sentiment_name'] = strategy_sentiment_name[send_backtest['strategy_sentiment']]
        send_backtest['source_name'] = source_name[send_backtest['source']]

        sql_sample_strategy = "SELECT * \
                                    FROM `strategy_backtest` \
                                    JOIN `stocks` \
                                    ON `strategy_backtest`.`stock_code` = `stocks`.`stock_code` \
                                    WHERE `user_id` = '20' \
                                    ORDER BY `create_date` DESC, `id` DESC \
                                    limit 15;"

        db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
        result = db_mysql.query_tb_all(sql_sample_strategy)
        # pprint(result[0])
        sample_strategy_form = [{
            'strategy_id': strategy_backtest[0],
            'user_id': strategy_backtest[1],
            'stock_code': strategy_backtest[2],
            'start_date': strategy_backtest[3],
            'end_date': strategy_backtest[4],
            'strategy_line': strategy_backtest[5],
            'strategy_in': strategy_backtest[6],
            'strategy_in_para': strategy_backtest[7],
            'strategy_out': strategy_backtest[8],
            'strategy_out_para': strategy_backtest[9],
            'strategy_sentiment': strategy_backtest[10],
            'source': strategy_backtest[11],
            'sentiment_para_more': strategy_backtest[12],
            'sentiment_para_less': strategy_backtest[13],
            'seed_money': strategy_backtest[14],
            'discount': strategy_backtest[15],
            'total_buy_count': strategy_backtest[16],
            'total_sell_count': strategy_backtest[17],
            'total_return_rate': strategy_backtest[18],
            'highest_return': strategy_backtest[19],
            'lowest_return': strategy_backtest[20],
            'total_win': strategy_backtest[21],
            'total_lose': strategy_backtest[22],
            'total_trade': strategy_backtest[23],
            'win_rate': strategy_backtest[24],
            'avg_return_rate': strategy_backtest[25],
            'irr': strategy_backtest[26],
            'file_path': strategy_backtest[27],
            'create_date': strategy_backtest[28],
            'stock_name': strategy_backtest[30],
            'category': strategy_backtest[31]
        } for strategy_backtest in result]
        sample_strategy_form_length = int(len(sample_strategy_form))
        # pprint(strategy_backtest_dict_list[0])
        print(sample_strategy_form)

        for sample_strategy in sample_strategy_form:
            sample_strategy['category_name'] = category_name[sample_strategy['category']]
            sample_strategy['strategy_line_name'] = strategy_line_name[sample_strategy['strategy_line']]
            sample_strategy['strategy_in_name'] = strategy_in_name[sample_strategy['strategy_in']]
            sample_strategy['strategy_out_name'] = strategy_out_name[sample_strategy['strategy_out']]
            sample_strategy['strategy_sentiment_name'] = strategy_sentiment_name[sample_strategy['strategy_sentiment']]
            sample_strategy['source_name'] = source_name[sample_strategy['source']]


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

    # https://dwkrd7hfr3x4e.cloudfront.net/backtest/22/2301_1637246115.png
    file_name = file_path.split("/")[-1]
    delete_file(BUCKET_NAME, OBJECT_PATH, user_id, file_name)

    return redirect(url_for('backtest.backtest_page'))
