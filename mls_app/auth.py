import functools
import secrets
from datetime import datetime, date

from flask import (Blueprint, abort, flash, g, redirect, render_template, url_for, request)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from .forms import *
from .db import *

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
login_manager = LoginManager()

"""required decorators"""


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    """redirect unauthorized user to login page"""
    return abort(404)


"""custom decorators"""


def empty_db(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        user = User.query.get(1)
        if user is None:
            return redirect(url_for('auth.register_first_user'))
        return view(*args, **kwargs)

    return wrapped_view


def super_admin_only(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user.user_type != 'super_admin':
            return abort(404)
        return view(*args, **kwargs)

    return wrapped_view


@auth_bp.route('/register_first_user=' + secrets.token_urlsafe(), methods=('GET', 'POST'))
def register_first_user():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.confirm.data:

            user = User(
                name=form.name.data,
                user_type='super_admin',
                email=form.email.data,
                encoded_by=form.name.data,
                encoded_on=datetime.now(),
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User successfully added')
            return redirect(url_for('auth.login'))
        elif form.cancel.data:
            flash('Registration aborted.', 'info')
            return redirect(url_for('auth.login'))
    return render_template('auth/register_first_user.html',
                           form=form,
                           title='mls-Register first user',
                           copyrightyear=datetime.now().year,
                           )


@auth_bp.route('/forget_password=' + secrets.token_urlsafe(), methods=('GET', 'POST'))
def forget_password():
    form1 = ForgetPasswordForm()

    if request.method == 'POST':
        if request.form.get('submit'):
            email = form1.email.data
            user_type = form1.user_type.data
            user = db.one_or_404(db.select(User).filter(
                User.email == email,
                User.user_type == user_type))

            # preload hidden field value on form2
            form2 = UpdatePasswordForm(request.values, user_id=user.id)
            return render_template('auth/password_update.html',
                                   form=form2,
                                   title='Update password',
                                   user=user)

        elif request.form.get('update'):

            # update password
            user = db.get_or_404(User, request.form.get('user_id'))
            user.edited_by = 'user'
            user.edited_on = datetime.now()
            user.set_password(request.form.get('password'))
            db.session.commit()
            flash('Password successfully updated.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/password_forget.html',
                           form=form1,
                           title='Forget password')


@auth_bp.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            user_type=form.user_type.data.lower(),
            email=form.email.data,
            encoded_by=current_user.name,
            encoded_on=datetime.now(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User successfully added')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',
                           form=form,
                           title='mls-Register',
                           copyrightyear=datetime.now().year,
                           )


@auth_bp.route('/delete_user/<user_name>', methods=('GET', 'POST'))
@login_required
def delete_user(user_name):
    # check encoding activities
    user = db.session.execute(db.select(User).filter(
        User.name == user_name
    )).scalar()

    if user.user_type != 'super_admin':
        dispatch_ = db.session.execute(db.select(Dispatch).filter(
            Dispatch.encoded_by == user_name
        )).scalar()

        if not dispatch_:
            maintenance_ = db.session.execute(db.select(Maintenance).filter(
                Maintenance.encoded_by == user_name
            )).scalar()

            if not maintenance_:
                expenses_ = db.session.execute(db.select(Expense).filter(
                    Expense.encoded_by == user_name
                )).scalar()

                if not expenses_:
                    vehicle_ = db.session.execute(db.select(Vehicle).filter(
                        Vehicle.encoded_by == user_name
                    )).scalar()

                    if not vehicle_:
                        tariff_ = db.session.execute(db.select(Tariff).filter(
                            Tariff.encoded_by == user_name
                        )).scalar()

                        if not tariff_:
                            employee_ = db.session.execute(db.select(Employee).filter(
                                Employee.encoded_by == user_name
                            )).scalar()

                            if not employee_:
                                invoice_ = db.session.execute(db.select(Invoice).filter(
                                    Invoice.edited_by == user_name
                                )).scalar()

                                if not invoice_:
                                    transaction_ = db.session.execute(db.select(Transaction).filter(
                                        Transaction.encoded_by == user_name
                                    )).scalar()

                                    # This user has not encoded anything. Ok to delete
                                    user_ = db.session.execute(db.select(User).filter(
                                        User.name == user_name
                                    )).scalar()

                                    db.session.delete(user_)
                                    db.session.commit()

                                    flash('User successfully delete', 'success')

                                    return redirect(url_for('admin_tool.user'))

    else:
        flash(f'Cannot delete this account.', 'danger')
        return redirect(url_for('admin_tool.user'))


@auth_bp.route('/login', methods=('GET', 'POST'))
@empty_db
def login():
    """logout out active user"""
    if current_user.is_active:
        logout_user()

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # verify user
        if user:
            if user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('user_profile'))
            else:
                error = 'Incorrect password!'
                flash(error, 'error')
                return redirect(url_for('auth.login'))
        else:
            error = 'This user does not exist'
            flash(error, 'error')
            return redirect(url_for('auth.login'))
    return render_template('auth/login.html',
                           form=form,
                           title='mls-Login',
                           copyrightyear=datetime.now().year,
                           )


@auth_bp.route('/logout', methods=('GET', 'POST'))
@login_required
def logout():
    user = User.query.get(current_user.id)
    user.last_login = datetime.now()
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))