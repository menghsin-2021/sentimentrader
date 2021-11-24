from flask import Flask, render_template, flash
import config
from model import model_mysql
from utils import get_cookie_check

from controller.social_volume import social_volume
from controller.sentiment import sentiment
from controller.strategy import strategy
from controller.backtest import backtest
from controller.user import user


# sever var
DEBUG = config.DEBUG
PORT = config.PORT
HOST = config.HOST
SECRET_KEY = config.SECRET_KEY


# create flask instance
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


# register api
app.register_blueprint(social_volume)
app.register_blueprint(sentiment)
app.register_blueprint(strategy)
app.register_blueprint(backtest)
app.register_blueprint(user)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

app.register_error_handler(404, page_not_found)


@app.route('/home.html', methods=['GET'])
def home():
    uid = get_cookie_check()
    print(uid)
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')
    else:
        return render_template('home.html')


if __name__ == "__main__":
    # initial db
    db_mysql = model_mysql.DbWrapperMysql('sentimentrader')
    # db_mysql.create_tb_all()


    # run sever
    app.run(debug=DEBUG, host=HOST, port=PORT)