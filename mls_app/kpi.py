from flask import Blueprint, render_template


kpi_bp = Blueprint('kpi', __name__, url_prefix='/kpi')


@kpi_bp.route('/dashboard', methods=('GET', 'POST'))
def dashboard():
    return render_template('kpi/dashboard.html')
