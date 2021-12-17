from flask import Blueprint, render_template, request, flash, redirect, url_for
from utils import get_cookie_check, StockSentimentFetch, GetName
import json
import config
from datetime import timedelta
import redis

REDIS_HOST = config.REDIS_HOST
REDIS_PORT = config.REDIS_PORT

# Blueprint
sentiment = Blueprint('sentiment', __name__, static_folder='static', template_folder='templates')


@sentiment.route('/sentiment.html')
def sentiment_page():
    token = request.cookies.get('token')
    # create fetch instance
    stock_sentiment_fetch = StockSentimentFetch()

    # set redis tag
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    tsmc_stock_code = '2330'
    source = 'cnyes'
    tag_stock_price, tag_sentiment = stock_sentiment_fetch.redis_tag(tsmc_stock_code, source)

    try:
        # fetch redis
        daily_stock_price = redis_client.get(tag_stock_price)
        daily_sentiment = redis_client.get(tag_sentiment)

    except:
        # redis over memory
        redis_client.flushall()
        daily_stock_price = stock_sentiment_fetch.fetch_stock_price(tsmc_stock_code)
        daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, tsmc_stock_code)


    else:
        if not daily_stock_price or not daily_sentiment:
            # fetch mysql
            daily_stock_price = stock_sentiment_fetch.fetch_stock_price(tsmc_stock_code)
            daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, tsmc_stock_code)

            # create redis value
            redis_store_daily_stock_price = json.dumps({'data': daily_stock_price}, indent=2, ensure_ascii=False)
            redis_store_daily_sentiment = json.dumps({'data': daily_sentiment}, indent=2, ensure_ascii=False)

            # set data
            redis_client.set(tag_stock_price, redis_store_daily_stock_price)
            redis_client.expire(tag_stock_price, timedelta(hours=2))
            redis_client.set(tag_sentiment, redis_store_daily_sentiment)
            redis_client.expire(tag_sentiment, timedelta(hours=2))

        else:
            # get redis data
            daily_stock_price = json.loads(redis_client.get(tag_stock_price))['data']
            daily_sentiment = json.loads(redis_client.get(tag_sentiment))['data']

    # set form info
    form_info = {
            'category': 'None',
            'category_name': '請選擇類股',
            'stock_code': '2330',
            'stock_name': '台積電',
            'source': 'cnyes',
            'source_name': '鉅亨網'
        }

    return render_template('sentiment.html', daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment, form_info=form_info, token=token)


@sentiment.route('/api/1.0/single_stock_sentiment', methods=['POST'])
def single_stock_sentiment():
    token = request.cookies.get('token')
    form = request.form.to_dict()
    category = form['category']

    if category == 'None':
        flash('請選擇類股', "error")
        return redirect(url_for('sentiment.sentiment_page'))

    stock_code = form['stock_code']
    source = form['source']

    # create fetch instance
    stock_sentiment_fetch = StockSentimentFetch()

    # link redis
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    try:
        # create key
        tag_stock_price, tag_sentiment = stock_sentiment_fetch.redis_tag(stock_code, source)

        # try fetch from redis
        daily_stock_price = redis_client.get(tag_stock_price)
        daily_sentiment = redis_client.get(tag_sentiment)

    except:
        # redis is crash => flushall
        redis_client.flushall()

        # fetch from mysql
        daily_stock_price = stock_sentiment_fetch.fetch_stock_price(stock_code)
        daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, stock_code)

    else:
        if not daily_stock_price or not daily_sentiment:
            # fetch stock price and sentiment
            daily_stock_price = stock_sentiment_fetch.fetch_stock_price(stock_code)
            daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, stock_code)

            # create redis value
            redis_store_daily_stock_price = json.dumps({'data': daily_stock_price}, indent=2, ensure_ascii=False)
            redis_store_daily_sentiment = json.dumps({'data': daily_sentiment}, indent=2, ensure_ascii=False)

            # set data
            redis_client.set(tag_stock_price, redis_store_daily_stock_price)
            redis_client.expire(tag_stock_price, timedelta(hours=2))
            redis_client.set(tag_sentiment, redis_store_daily_sentiment)
            redis_client.expire(tag_sentiment, timedelta(hours=2))

        else:
            # get redis data
            daily_stock_price = json.loads(redis_client.get(tag_stock_price))['data']
            daily_sentiment = json.loads(redis_client.get(tag_sentiment))['data']


    form_info = form

    get_name = GetName()
    form_info['category_name'] = get_name.category(form_info['category'])
    form_info['source_name'] = get_name.source(form_info['source'])
    form_info['stock_name'] = daily_sentiment['chosen_stock_name']


    return render_template('sentiment.html', daily_stock_price=daily_stock_price, daily_sentiment=daily_sentiment, form_info=form_info, token=token)


@sentiment.route('/api/1.0/set_sentiment_cache', methods=['POST'])
def set_sentiment_cache():
    try:
        form = request.form.to_dict()
        stock_code = form['stock_code']
        source = form['source']
        secret_key = form['secret_key']

    except:
        pass

    else:
        if secret_key == config.SECRET_KEY:
            # create fetch instance
            stock_sentiment_fetch = StockSentimentFetch()

            # fetch stock price and sentiment
            daily_stock_price = stock_sentiment_fetch.fetch_stock_price(stock_code)
            daily_sentiment = stock_sentiment_fetch.fetch_sentiment(source, stock_code)

            # link redis
            redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

            # create key
            tag_stock_price, tag_sentiment = stock_sentiment_fetch.redis_tag(stock_code, stock_code)

            # create value
            redis_store_daily_stock_price = json.dumps({'data': daily_stock_price}, indent=2, ensure_ascii=False)
            redis_store_daily_sentiment = json.dumps({'data': daily_sentiment}, indent=2, ensure_ascii=False)

            # set data
            redis_client.set(tag_stock_price, redis_store_daily_stock_price)
            redis_client.set(tag_sentiment, redis_store_daily_sentiment)

        else:
            pass

    return render_template('login.html')