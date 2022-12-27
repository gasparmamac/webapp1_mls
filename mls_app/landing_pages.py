import datetime

from flask import Blueprint, render_template, session
from flask_login import login_required


landing_bp = Blueprint('', __name__, url_prefix='/landing_page')


@landing_bp.route('/', methods=('GET', 'POST'))
def index():
    year = datetime.datetime.now().year
    return render_template('landing_pages/index.html',
                           title='mls - Welcome!',
                           copyright_year=year)


@landing_bp.route('/user_profile', methods=('GET', 'POST'))
@login_required
def user_profile():
    # initialize session values
    session['maintenance_filtered'] = False
    session['dispatch_filtered'] = False
    session['invoice_filtered'] = False
    year = datetime.datetime.now().year
    return render_template('landing_pages/user_profile.html',
                           title='mls-User profile',
                           copyright_year=year)


@landing_bp.route('/contact', methods=('GET', 'POST'))
def contact():
    year = datetime.datetime.now().year
    return render_template('landing_pages/contact.html',
                           title='mls-Contact',
                           copyright_year=year)


@landing_bp.route('/about', methods=('GET', 'POST'))
def about():
    year = datetime.datetime.now().year
    return render_template('landing_pages/about.html',
                           title='mls-About',
                           copyright_year=year)
