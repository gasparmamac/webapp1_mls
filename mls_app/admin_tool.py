
from datetime import date
import functools
import pandas as pd

from flask import Blueprint, render_template, redirect, url_for, abort, request, flash, session
from flask_login import login_required
from sqlalchemy import desc, exc

from .db import *
from .forms import *
from .my_util_funct import *

admin_tool_bp = Blueprint('admin_tool', __name__, url_prefix='/admin_tool')


@admin_tool_bp.route('/employee', methods=('GET', 'POST'))
@login_required
def employee():
    data = Employee.query.all()
    page = db.paginate(db.select(Employee).order_by(Employee.encoded_on))
    year = date.today().year
    return render_template('admin_tool/employee.html',
                           object=Employee,
                           data=data,
                           page=page,
                           title='mls-Employee',
                           copyright_year=year)


@admin_tool_bp.route('/employee_add', methods=('GET', 'POST'))
@login_required
def employee_add():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            if form.confirm.data:
                new_emp = Employee(
                    first_name=form.first_name.data.lower(),
                    middle_name=form.middle_name.data.lower(),
                    last_name=form.last_name.data.lower(),
                    birthday=form.birthday.data,
                    mobile_no=form.mobile_no.data,
                    sss=form.sss.data,
                    phil_health=form.phil_health.data,
                    pag_ibig=form.pag_ibig.data,
                    status=form.status.data.lower(),
                    rate=form.rate.data,
                    allowance=form.allowance.data,
                    encoded_by=current_user.name,
                    encoded_on=date.today(),
                )
                db.session.add(new_emp)
                db.session.commit()
                flash(f'Row #{new_emp.id} added successfully', 'success')
                return redirect(url_for('admin_tool.employee'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('admin_tool.employee_add'))
    year = date.today().year
    return render_template('admin_tool/employee_add.html',
                           form=form,
                           title='mls-Employee_add',
                           copyright_year=year)


@admin_tool_bp.route('/employee_edit/<int:emp_id>', methods=('GET', 'POST'))
@login_required
def employee_edit(emp_id):
    edit_emp = Employee.query.get(emp_id)
    # fill-up form
    edit_form = EmployeeForm(
        first_name=edit_emp.first_name,
        middle_name=edit_emp.middle_name,
        last_name=edit_emp.last_name,
        birthday=edit_emp.birthday,
        mobile_no=edit_emp.mobile_no,
        sss=edit_emp.sss,
        phil_health=edit_emp.phil_health,
        pag_ibig=edit_emp.pag_ibig,
        rate=edit_emp.rate,
        allowance=edit_emp.allowance
    )

    if edit_form.validate_on_submit():
        try:
            if edit_form.confirm.data:
                edit_emp.first_name = edit_form.first_name.data.lower()
                edit_emp.middle_name = edit_form.middle_name.data.lower()
                edit_emp.last_name = edit_form.last_name.data.lower()
                edit_emp.birthday = edit_form.birthday.data
                edit_emp.mobile_no = edit_form.mobile_no.data
                edit_emp.sss = edit_form.sss.data
                edit_emp.phil_health = edit_form.phil_health.data
                edit_emp.pag_ibig = edit_form.pag_ibig.data
                edit_emp.rate = edit_form.rate.data
                edit_emp.allowance = edit_form.allowance.data
                edit_emp.edited_by = current_user.name
                edit_emp.edited_on = date.today()
                db.session.commit()
                flash(f'Row #{edit_emp.id} edited successfully', 'success')
                return redirect(url_for('admin_tool.employee'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('admin_tool.employee_edit'))

    year = date.today().year
    return render_template('admin_tool/employee_edit.html',
                           form=edit_form,
                           title='mls-Employee_edit',
                           copyright_year=year)


@admin_tool_bp.route('/employee_view/<int:emp_id>', methods=('GET', 'POST'))
@login_required
def employee_view(emp_id):
    emp = pd.read_sql_table('employee', db.engine, index_col='id')
    data_emp = emp.loc[emp_id]
    year = date.today().year
    return render_template('admin_tool/employee_view.html',
                           data=data_emp,
                           title='mls-Employee_view',
                           copyright_year=year)


@admin_tool_bp.route('/employee_delete/<int:emp_id>', methods=('GET', 'POST'))
@login_required
def employee_delete(emp_id):
    emp_id = emp_id
    emp_to_delete = Employee.query.get(emp_id)
    emp_payrolls = emp_to_delete.payrolls

    # prohibit delete if has entry on children
    if emp_payrolls:
        flash(f'Cannot delete this employee. He/she is included in {len(emp_payrolls)} payrolls', 'danger')
        return redirect(url_for('admin_tool.employee'))

    if request.method == 'POST':
        if request.form.get('delete_button') == 'confirm':
            db.session.delete(emp_to_delete)
            db.session.commit()
            flash(f'Row #{emp_id} deleted successfully.', 'success')
            return redirect(url_for('admin_tool.employee'))
        elif request.form.get('delete_button') == 'cancel':
            flash('Delete operation aborted.', 'info')
            return redirect(url_for('admin_tool.employee'))
    year = date.today().year
    return render_template('admin_tool/employee_delete.html',
                           emp_id=emp_id,
                           title='mls-Employee_delete',
                           copyright_year=year)


@admin_tool_bp.route('/tariff', methods=('GET', 'POST'))
@login_required
def tariff():
    data = Tariff.query.all()
    page = db.paginate(db.select(Tariff).order_by(Tariff.encoded_on))
    year = date.today().year
    return render_template('admin_tool/tariff.html',
                           object=Tariff,
                           data=data,
                           page=page,
                           title='mls-Tariff',
                           copyright_year=year)


@admin_tool_bp.route('/tariff_add', methods=('GET', 'POST'))
@login_required
def tariff_add():
    # check for encoded vehicle
    vehicle_exist = Vehicle.query.get(1)
    if not vehicle_exist:
        flash('Add a vehicle first before you add a tariff rate.', 'info')
        return redirect(url_for('admin_tool.vehicle'))

    form = TariffForm()
    choices = [item.model for item in Vehicle.query.order_by('id')]
    form.vehicle_model.choices = remove_duplicate(choices)
    if form.validate_on_submit():
        try:
            new_tariff = Tariff(
                area=form.area.data.lower(),
                destination=form.destination.data.lower(),
                km=form.km.data,
                vehicle_model=form.vehicle_model.data,
                rate=form.rate.data,
                encoded_by=current_user.name,
                encoded_on=date.today()
            )
            db.session.add(new_tariff)
            db.session.commit()
            flash(f'Row #{new_tariff.id} added successfully', 'success')
            return redirect(url_for('admin_tool.tariff'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('admin_tool.tariff_add'))

    year = date.today().year
    return render_template('admin_tool/tariff_add.html',
                           form=form,
                           title='mls-Tariff_add',
                           copyright_year=year)


@admin_tool_bp.route('/tariff_delete/<int:tariff_id>', methods=('GET', 'POST'))
@login_required
def tariff_delete(tariff_id):
    tariff_id = tariff_id

    tariff_to_delete = Tariff.query.get(tariff_id)
    tariff_dispatches = tariff_to_delete.dispatches

    # prohibit delete if has entry on children
    if tariff_dispatches:
        flash(f'Cannot delete this tariff. It is used in {len(tariff_dispatches)} dispatches', 'danger')
        return redirect(url_for('admin_tool.tariff'))

    else:
        if request.method == 'POST':
            if request.form.get('delete_button') == 'confirm':
                db.session.delete(tariff_to_delete)
                db.session.commit()
                flash(f'Row #{tariff_id} deleted successfully.', 'success')
                return redirect(url_for('admin_tool.tariff'))
            elif request.form.get('delete_button') == 'cancel':
                flash('Delete operation aborted.', 'info')
                return redirect(url_for('admin_tool.tariff'))
    year = date.today().year
    return render_template('admin_tool/tariff_delete.html',
                           tariff_id=tariff_id,
                           title='mls-Tariff_delete',
                           copyright_year=year)


@admin_tool_bp.route('/tariff_edit/<int:tariff_id>', methods=('GET', 'POST'))
@login_required
def tariff_edit(tariff_id):
    edit_tariff = Tariff.query.get(tariff_id)
    # fill-up form
    edit_form = TariffForm(
        area=edit_tariff.area,
        destination=edit_tariff.destination,
        km=edit_tariff.km,
        vehicle_type=edit_tariff.vehicle_model,
        rate=edit_tariff.rate,
    )
    choices = [item.model for item in Vehicle.query.order_by('id')]
    edit_form.vehicle_model.choices = remove_duplicate(choices)
    if edit_form.validate_on_submit():
        try:
            if edit_form.confirm.data:
                edit_tariff.area = edit_form.area.data.lower()
                edit_tariff.destination = edit_form.destination.data.lower()
                edit_tariff.km = edit_form.km.data
                edit_tariff.vehicle_model = edit_form.vehicle_model.data
                edit_tariff.rate = edit_form.rate.data
                edit_tariff.edited_by = current_user.name
                edit_tariff.edited_on = date.today()
                db.session.commit()
                flash(f'Row #{edit_tariff.id} edited successfully', 'success')
                return redirect(url_for('admin_tool.tariff'))
        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not edited!', 'danger')
            return redirect(url_for('admin_tool.tariff_edit'))

    year = date.today().year
    return render_template('admin_tool/tariff_edit.html',
                           form=edit_form,
                           title='mls-Tariff_edit',
                           copyright_year=year)


@admin_tool_bp.route('/tariff_view/<int:tariff_id>', methods=('GET', 'POST'))
@login_required
def tariff_view(tariff_id):
    tar = pd.read_sql_table('tariff', db.engine, index_col='id')
    data_tariff = tar.loc[tariff_id]
    year = date.today().year
    return render_template('admin_tool/tariff_view.html',
                           data=data_tariff,
                           title='mls-Tariff_view',
                           copyright_year=year)


@admin_tool_bp.route('/vehicle', methods=('GET', 'POST'))
@login_required
def vehicle():
    data = Vehicle.query.all()
    page = db.paginate(db.select(Vehicle).order_by('id'))
    year = date.today().year
    return render_template('admin_tool/vehicle.html',
                           object=Vehicle,
                           data=data,
                           page=page,
                           title='mls-Vehicle',
                           copyright_year=year)


@admin_tool_bp.route('/vehicle_add', methods=('GET', 'POST'))
@login_required
def vehicle_add():
    form = VehicleForm()
    if form.validate_on_submit():
        try:
            new_vehicle = Vehicle(
                maker=form.maker.data.lower(),
                model=form.model.data.lower(),
                year=form.year.data,
                plate_no=form.plate_no.data,
                last_registration=form.last_registration.data,
                odo=form.odo.data,
                odo_updated=form.odo_updated.data,
                encoded_by=current_user.name,
                encoded_on=date.today()
            )
            db.session.add(new_vehicle)
            db.session.commit()
            flash(f'Row #{new_vehicle.id} added successfully', 'success')
            return redirect(url_for('admin_tool.vehicle'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('admin_tool.vehicle_add'))

    year = date.today().year
    return render_template('admin_tool/vehicle_add.html',
                           form=form,
                           title='mls-Vehicle_add',
                           copyright_year=year)


@admin_tool_bp.route('/vehicle_edit/<int:vehicle_id>', methods=('GET', 'POST'))
@login_required
def vehicle_edit(vehicle_id):
    edit_vehicle = Vehicle.query.get(vehicle_id)
    # fill-up form
    edit_form = VehicleForm(
        maker=edit_vehicle.maker,
        model=edit_vehicle.model.lower(),
        year=edit_vehicle.year.lower(),
        plate_no=edit_vehicle.plate_no.lower(),
        last_registration=edit_vehicle.last_registration,
        odo=edit_vehicle.odo,
        odo_updated=edit_vehicle.odo_updated,
    )
    if edit_form.validate_on_submit():
        try:
            if edit_form.confirm.data:
                edit_vehicle.maker = edit_form.maker.data.lower()
                edit_vehicle.model = edit_form.model.data.lower()
                edit_vehicle.year = edit_form.year.data.lower()
                edit_vehicle.plate_no = edit_form.plate_no.data.lower()
                edit_vehicle.last_registration = edit_form.last_registration.data
                edit_vehicle.odo = edit_form.odo.data
                edit_vehicle.odo_updated = edit_form.odo_updated.data
                edit_vehicle.edited_by = current_user.name
                edit_vehicle.edited_on = date.today()
                db.session.commit()
                flash(f'Row #{edit_vehicle.id} edited successfully', 'success')
                return redirect(url_for('admin_tool.vehicle'))
        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not edited!', 'danger')
            return redirect(url_for('admin_tool.vehicle_edit'))

    year = date.today().year
    return render_template('admin_tool/vehicle_edit.html',
                           form=edit_form,
                           title='mls-Vehicle_edit',
                           copyright_year=year)


@admin_tool_bp.route('/vehicle_delete/<int:vehicle_id>', methods=('GET', 'POST'))
@login_required
def vehicle_delete(vehicle_id):
    vehicle_id = vehicle_id
    vehicle_to_delete = Vehicle.query.get(vehicle_id)
    vehicle_dispatches = vehicle_to_delete.dispatches

    # prohibit delete if has entry on children
    if vehicle_dispatches:
        flash(f'Cannot delete this vehicle. It has {len(vehicle_dispatches)} dispatches', 'danger')
        return redirect(url_for('admin_tool.vehicle'))
    else:
        if request.method == 'POST':
            if request.form.get('delete_button') == 'confirm':
                db.session.delete(vehicle_to_delete)
                db.session.commit()
                flash(f'Row #{vehicle_id} deleted successfully.', 'success')
                return redirect(url_for('admin_tool.vehicle'))
            elif request.form.get('delete_button') == 'cancel':
                flash('Delete operation aborted.', 'info')
                return redirect(url_for('admin_tool.vehicle'))
    year = date.today().year

    return render_template('admin_tool/vehicle_delete.html',
                           vehicle_id=vehicle_id,
                           title='mls-Vehicle_delete',
                           copyright_year=year)


@admin_tool_bp.route('/vehicle_view/<int:vehicle_id>', methods=('GET', 'POST'))
@login_required
def vehicle_view(vehicle_id):
    vehicle_df = pd.read_sql_table('vehicle', db.engine, index_col='id')
    data_vehicle = vehicle_df.loc[vehicle_id]
    year = date.today().year
    return render_template('admin_tool/vehicle_view.html',
                           data=data_vehicle,
                           title='mls-Vehicle_view',
                           copyright_year=year)


@admin_tool_bp.route('/transaction', methods=('GET', 'POST'))
@login_required
def transaction():
    """payroll"""
    df_unpaid_disp = pd.read_sql_query(db.select(Dispatch).order_by(desc('plate_no')).filter_by(payroll_id=None),
                                       con=db.engine, index_col='id')
    employees = db.session.execute(db.select(Employee).order_by('last_name')).scalars()
    payroll_list, payroll_total = compute_emp_payroll(employees)

    """maintenance"""
    df_maintenance = pd.read_sql_query(db.select(Maintenance).order_by(desc('date')).filter_by(transaction_id=None),
                                       con=db.engine, index_col='id')
    maintenance_total = df_maintenance['amount'].sum()

    """expenses"""
    df_expense = pd.read_sql_query(db.select(Expense).order_by(desc('date')).filter_by(transaction_id=None),
                                   con=db.engine, index_col='id')
    expense_total = df_expense['amount'].sum()

    """grand total"""
    grand_total = payroll_total + maintenance_total + expense_total

    session['grand_total'] = grand_total
    session['payroll_total'] = payroll_total
    session['empty_dispatch'] = df_unpaid_disp.empty
    session['empty_maintenance'] = df_maintenance.empty
    session['empty_expense'] = df_expense.empty
    return render_template('admin_tool/transaction.html',
                           title='Transaction',
                           df_unpaid_disp=df_unpaid_disp,
                           payroll_list=payroll_list,
                           payroll_total=payroll_total,
                           df_maintenance=df_maintenance,
                           maintenance_total=maintenance_total,
                           df_expense=df_expense,
                           expense_total=expense_total,
                           grand_total=grand_total,
                           )


@admin_tool_bp.route('/transaction_pay_now', methods=('GET', 'POST'))
@login_required
def transaction_pay_now():
    form = TransactionForm()
    if form.validate_on_submit():
        if form.cancel.data:
            flash('Transaction cancelled!', 'danger')
            return redirect(url_for('admin_tool.transaction'))

        if form.proceed.data:
            # update transaction
            new_transaction = Transaction(
                date=date.today(),
                remarks=form.remarks.data,
                encoded_by=current_user.name,
                encoded_on=date.today()
            )
            db.session.add(new_transaction)

            """update payroll"""
            if not session.get('empty_dispatch'):
                no_payroll_disp = db.session.execute(db.select(Dispatch).filter_by(payroll_id=None)).scalars()

                new_payroll = Payroll(
                    date=date.today(),
                    amount=session.get('payroll_total'),
                    transaction_id=new_transaction.id,
                    encoded_by=current_user.name,
                    encoded_on=date.today()
                )
                db.session.add(new_payroll)

                """update dispatch and emp_table"""
                for disp in no_payroll_disp:
                    emp_list = [emp for emp in disp.employees]
                    disp.payroll_id = new_payroll.id

                emp_list_clean = remove_duplicate(emp_list)
                for emp in emp_list_clean:
                    new_payroll.employees.append(emp)

            """update maintenance"""
            if not session.get('empty_maintenance'):
                _main = db.session.execute(db.select(Maintenance).filter(Maintenance.transaction_id == None)).scalars()
                for main in _main:
                    main.transaction_id = new_transaction.id

            """update expense"""
            if not session.get('empty_expense'):
                _exp = db.session.execute(db.select(Expense).filter(Expense.transaction_id == None)).scalars()
                for exp in _exp:
                    exp.transaction_id = new_transaction.id

            # commit changes
            db.session.commit()

            # release session variables
            session.pop('grand_total', None)
            session.pop('payroll_total', None)
            session.pop('empty_dispatch', None)
            session.pop('empty_maintenance', None)
            session.pop('empty_expense', None)

            flash('Transaction successfully processed.', 'success')
            return redirect(url_for('admin_tool.transaction'))

    return render_template('admin_tool/transaction_pay_now.html',
                           title='Transaction_pay_now',
                           form=form)


@admin_tool_bp.route('/transaction_view', methods=('GET', 'POST'))
@login_required
def transaction_view():
    data = db.paginate(db.select(Transaction).order_by(desc('date')), per_page=3, max_per_page=3)
    return render_template('admin_tool/transaction_view.html',
                           title='Transaction_view',
                           data=data,
                           )


@admin_tool_bp.route('/payroll_view/<int:payroll_id>', methods=('GET', 'POST'))
@login_required
def payroll_view(payroll_id):
    datum = db.get_or_404(Payroll, payroll_id)
    return render_template('admin_tool/payroll_view.html',
                           title='Payroll_view',
                           datum=datum
                           )


@admin_tool_bp.route('/transaction_pdf/<int:transaction_id>', methods=('GET', 'POST'))
@login_required
def transaction_pdf(transaction_id):
    datum = db.get_or_404(Transaction, transaction_id)
    return f'data: {datum}'


@admin_tool_bp.route('user', methods=('GET', 'POST'))
@login_required
def user():
    page = db.paginate(db.select(User).order_by('name'))
    year = date.today().year
    return render_template('admin_tool/user.html',
                           page=page,
                           object=User,
                           title='mls-User',
                           copyright_year=year)
