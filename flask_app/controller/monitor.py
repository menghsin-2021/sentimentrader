from flask import Blueprint, Response, render_template, request, flash
from utils import get_cookie_check
import json

# Blueprint
monitor = Blueprint('monitor', __name__, static_folder='static', template_folder='templates')



@monitor.route('/monitor.html', methods=['GET'])
def monitor_page():
    uid = get_cookie_check()
    if isinstance(uid, int) is False:
        flash('需要登入', 'danger')
        return render_template('login.html')


    return "monitor"

