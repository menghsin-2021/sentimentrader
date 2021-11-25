from flask import Blueprint, render_template, request, flash, redirect, url_for, make_response, Response
from datetime import datetime, timedelta

from model import model_mysql
import config
from utils import Checkjwt

from model import model_mysql_query


# Blueprint
user = Blueprint('user', __name__, static_folder='static', template_folder='templates')

# secret key
SECRET_KEY = config.SECRET_KEY

check_jwt = Checkjwt()

DBNAME = config.DBNAME

@user.route('/', methods=['GET'])
@user.route('/login.html', methods=['GET'])
def login():
    return render_template('login.html')


@user.route('/api/1.0/signup', methods=['POST'])
def signup():
    # get request data
    user_signup_request = request.form.to_dict()
    name = user_signup_request['name']
    email = user_signup_request['email']
    pwd = user_signup_request['pwd']
    con_pwd = user_signup_request['con-pwd']

    # db initialize
    db_mysql = model_mysql.DbWrapperMysql(DBNAME)

    # check Basic Auth
    basic_auth = check_jwt.check_basic_auth_signup(name, email, pwd, con_pwd)
    if not basic_auth:
        flash('兩次密碼輸入不同', 'error')
        return redirect(url_for('user.login'))

    else:
        # search email if exist
        sql_email = "SELECT `id` FROM `user` WHERE `email`= %s"
        result_email = db_mysql.query_tb_one(sql_email, (email,))

        if result_email:
            db_mysql.close_db()
            flash('這個信箱已註冊過', 'error')
            return redirect(url_for('user.login'))

        else:
            # salt password
            password_salt = check_jwt.generate_salt()
            password_hash = check_jwt.generate_hash(pwd, password_salt)

            # set token
            iss = 'stock-sentimentrader.com'
            sub = email
            aud = 'www.stock-sentimentrader.com'
            iat = datetime.utcnow()
            nbf = datetime.utcnow()
            exp = iat + timedelta(seconds=3600)
            jti = email

            access_token = check_jwt.set_token(iss, sub, aud, iat, nbf, exp, jti)
            access_token_str = check_jwt.b_type_to_str(access_token)
            access_expired = int(exp.timestamp()-iat.timestamp())

            # insert db
            sql_insert_user = model_mysql_query.sql_insert_user
            db_mysql.insert_tb(sql_insert_user, (name, email, password_hash, password_salt, access_token, access_expired))

            # send token back
            signup_user_info = {'data': {'access_token': access_token_str,  # 不能傳 byte 格式
                                              'access_expired': access_expired,
                                              'user': {
                                                  'name': name,
                                                  'email': email,
                                              }}}

            resp = make_response(redirect(url_for('home')))
            resp.set_cookie(key='token', value=signup_user_info['data']['access_token'])
            flash('註冊成功', 'success')
            return resp


@user.route('/api/1.0/signin', methods=['POST'])
def signin():
    user_signin_request = request.form.to_dict()
    print(user_signin_request)

    email = user_signin_request['email']
    pwd = user_signin_request['pwd']

    basic_auth = check_jwt.check_basic_auth_signin(email, pwd)

    if not basic_auth:
        flash('輸入長度過長', 'error')
        return redirect(url_for('user.login'))
    else:
        db_mysql = model_mysql.DbWrapperMysqlDict(DBNAME)
        sql_email = "SELECT `id`, `name`, `email`, `password`, `password_salt` FROM `user` WHERE `email`= %s"
        result = db_mysql.query_tb_one(sql_email, (email,))
        if not result:
            flash('此信箱未被註冊，請重新輸入', 'error')
            return redirect(url_for('user.login'))
        else:
            db_id = result['id']
            db_name = result['name']
            db_email = result['email']
            db_password = result['password']
            db_password_salt = result['password_salt']
            # password salt
            password_salt = db_password_salt
            password_hash = check_jwt.generate_hash(pwd, password_salt)
            if db_password != password_hash:
                return Response('error: wrong password', status=403)
            else:
                # set token
                iss = 'stock-sentimentrader.com'
                sub = db_email
                aud = 'www.stock-sentimentrader.com'
                iat = datetime.utcnow()
                nbf = datetime.utcnow()
                exp = iat + timedelta(seconds=3600)
                jti = email
                access_token = check_jwt.set_token(iss, sub, aud, iat, nbf, exp, jti)
                access_token_str = check_jwt.b_type_to_str(access_token)
                access_expired = int(exp.timestamp() - iat.timestamp())

                sql_update = "UPDATE `user` SET `access_token`=%s, `access_expired`=%s WHERE `email`=%s"
                db_mysql.update_tb(sql_update, (access_token, access_expired, email))
                db_mysql.close_db()

                # 回傳token
                signin_user_info = {'data': {'access_token': access_token_str,  # can't send b type
                                             'access_expired': access_expired,
                                             'user': {
                                                 'id': db_id,
                                                 'name': db_name,
                                                 'email': db_email,
                                             }}}


                resp = make_response(redirect(url_for('home')))
                resp.set_cookie(key='token', value=signin_user_info['data']['access_token'])

                return resp


@user.route('/logout', methods=['GET'])
def logout():
    resp = make_response(render_template('login.html'))
    resp.delete_cookie('token')
    return resp