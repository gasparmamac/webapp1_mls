from datetime import datetime, date
import functools
import pandas as pd

from flask import Blueprint, render_template, redirect, url_for, abort, request, flash, session, g
from flask_login import current_user, login_required
from sqlalchemy import desc, exc

from .db import *
from .forms import *
from .my_util_funct import remove_duplicate

encoder_tool_bp = Blueprint('encoder_tool', __name__, url_prefix='/encode_tool')


@encoder_tool_bp.route('/expenses', methods=('GET', 'POST'))
@login_required
def expenses():
    table_row_per_page = 10
    form = FilterForm2()

    # form choices
    form.transaction.choices = ['-none-', '-all-']

    if form.validate_on_submit():
        # store form data to session varaibles
        session['expense_filter_from_'] = form.from_.data.isoformat()
        session['expense_filter_to_'] = form.to_.data.isoformat()
        session['expense_filter_transaction'] = form.transaction.data
        session['expense_filtered'] = True
        return redirect(url_for('encoder_tool.expenses'))

    elif session.get('expense_filtered'):
        # retrieve data from session variables
        val1 = date.fromisoformat(session.get('expense_filter_from_'))
        val2 = date.fromisoformat(session.get('expense_filter_to_'))
        val4 = session.get('expense_filter_transaction')

        # pre-load filter values
        form = FilterForm1(
            from_=val1,
            to_=val2,
            transaction=val4,
        )

        # form choices
        form.transaction.choices = ['-all-', '-none-']

        # select data with filter value
        if val4 == '-all-':
            data = db.paginate(db.select(Expense).order_by(desc('date')).filter(
                Expense.date.between(val1, val2),
            ), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'

        elif val4 == '-none-':
            data = db.paginate(db.select(Expense).order_by(desc('date')).filter(
                Expense.date.between(val1, val2),
                Expense.transaction_id == None,
            ), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'

    else:
        data = db.paginate(db.select(Expense).order_by(desc('date')), per_page=table_row_per_page)
        table_caption = f'page: {data.page} of {data.pages}'

    year = date.today().year
    return render_template('encoder_tool/expenses.html',
                           form=form,
                           table_caption=table_caption,
                           object=Expense,
                           page=data,
                           data=data,
                           title='mls-Expenses',
                           copyright_year=year)


@encoder_tool_bp.route('/expenses_add', methods=('GET', 'POST'))
@login_required
def expenses_add():
    form = ExpenseForm()
    if form.validate_on_submit():
        try:
            if form.confirm.data:
                new_exp = Expense(
                    date=form.date.data,
                    amount=form.amount.data,
                    purpose=form.purpose.data.lower(),
                    encoded_by=current_user.name,
                    encoded_on=date.today()
                )
                db.session.add(new_exp)
                db.session.commit()
                flash(f'Row #{new_exp.id} added successfully', 'success')
                return redirect(url_for('encoder_tool.expenses'))
        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('encoder_tool.expenses_add'))

    year = date.today().year
    return render_template('encoder_tool/expenses_add.html',
                           form=form,
                           title='mls-Expenses_add',
                           copyright_year=year)


@encoder_tool_bp.route('/expenses_delete/<int:expense_id>', methods=('GET', 'POST'))
@login_required
def expenses_delete(expense_id):
    expense_to_delete = Expense.query.get(expense_id)
    if expense_to_delete.transaction_id:
        transaction_id = expense_to_delete.transaction_id
        flash(f'Cannot delete this expense. It is included in TRANSACTION#:{transaction_id}', 'danger')
        return redirect(url_for('encoder_tool.dispatch'))

    expense_id = expense_id
    if request.method == 'POST':
        if request.form.get('delete_button') == 'confirm':
            db.session.delete(expense_to_delete)
            db.session.commit()
            flash(f'Row #{expense_id} deleted successfully.', 'success')
            return redirect(url_for('encoder_tool.expenses'))
        elif request.form.get('delete_button') == 'cancel':
            flash('Delete operation aborted.', 'info')
            return redirect(url_for('encoder_tool.expenses'))

    year = date.today().year
    return render_template('encoder_tool/expenses_delete.html',
                           expense_id=expense_id,
                           title='mls-Expenses_delete',
                           copyright_year=year)


@encoder_tool_bp.route('/expenses_edit/<int:expense_id>', methods=('GET', 'POST'))
@login_required
def expenses_edit(expense_id):
    edit_expense = Expense.query.get(expense_id)
    # fill-up form
    edit_form = ExpenseForm(
        date=edit_expense.date,
        amount=edit_expense.amount,
        purpose=edit_expense.purpose,

    )

    if edit_form.validate_on_submit():
        try:
            if edit_form.confirm.data:
                edit_expense.date = edit_form.date.data
                edit_expense.amount = edit_form.amount.data
                edit_expense.purpose = edit_form.purpose.data.lower()
                edit_expense.edited_by = current_user.name
                edit_expense.edited_on = date.today()
                db.session.commit()
                flash(f'Row #{edit_expense.id} edited successfully', 'success')
                return redirect(url_for('encoder_tool.expenses'))
        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not edited!', 'danger')
            return redirect(url_for('encoder_tool.expenses_edit'))

    year = date.today().year
    return render_template('encoder_tool/expenses_edit.html',
                           form=edit_form,
                           title='mls-Expenses_edit',
                           copyright_year=year)


@encoder_tool_bp.route('/expenses_view/<int:expense_id>', methods=('GET', 'POST'))
@login_required
def expenses_view(expense_id):
    exp = pd.read_sql_table('expenses', db.engine, index_col='id')
    data_expenses = exp.loc[expense_id]
    year = date.today().year
    return render_template('encoder_tool/expenses_view.html',
                           data=data_expenses,
                           title='mls-Expenses_view',
                           copyright_year=year)


@encoder_tool_bp.route('/maintenance/', methods=('GET', 'POST'))
@login_required
def maintenance():
    table_row_per_page = 10
    form = FilterForm1()

    # form choices
    choices_vehicle = [item.plate_no for item in db.session.execute(db.select(Maintenance)).scalars()]
    choices_vehicle.insert(0, '-all-')
    choices_vehicle.insert(1, '-none-')
    form.vehicle.choices = remove_duplicate(choices_vehicle)
    form.transaction.choices = ['-all-', '-none-']

    if form.validate_on_submit():
        # store form data to session variables
        session['maintenance_filter_from_'] = form.from_.data.isoformat()
        session['maintenance_filter_to_'] = form.to_.data.isoformat()
        session['maintenance_filter_vehicle'] = form.vehicle.data
        session['maintenance_filter_transaction'] = form.transaction.data
        session['maintenance_filtered'] = True
        return redirect(url_for('encoder_tool.maintenance'))

    elif session.get('maintenance_filtered'):
        # retrieve data from session variables
        val1 = date.fromisoformat(session.get('maintenance_filter_from_'))
        val2 = date.fromisoformat(session.get('maintenance_filter_to_'))
        val3 = session.get('maintenance_filter_vehicle')
        val4 = session.get('maintenance_filter_transaction')

        # pre-load filter values
        form = FilterForm1(
            from_=val1,
            to_=val2,
            vehicle=val3,
            transaction=val4,
        )

        # form choices
        choices_vehicle = [item.plate_no for item in db.session.execute(db.select(Maintenance)).scalars()
                           if item.plate_no is not None]
        choices_vehicle.insert(0, '-all-')
        choices_vehicle.insert(1, '-none-')
        form.vehicle.choices = remove_duplicate(choices_vehicle)
        form.transaction.choices = ['-all-', '-none-']

        # select data with filter value
        if val4 == '-all-':
            if val3 == '-all-':
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            elif val3 == '-none-':
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                    Maintenance.plate_no == None,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            else:
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                    Maintenance.plate_no == val3,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'

        elif val4 == '-none-':
            if val3 == '-all-':
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                    Maintenance.transaction_id == None,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            elif val3 == '-none-':
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                    Maintenance.plate_no == None,
                    Maintenance.transaction_id == None,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            else:
                data = db.paginate(db.select(Maintenance).order_by(desc('date')).filter(
                    Maintenance.date.between(val1, val2),
                    Maintenance.plate_no == val3,
                    Maintenance.transaction_id == None,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'

    else:
        data = db.paginate(db.select(Maintenance).order_by(desc('date')), per_page=table_row_per_page)
        table_caption = f'page: {data.page} of {data.pages}'
    year = date.today().year
    return render_template('encoder_tool/maintenance.html',
                           form=form,
                           object=Maintenance,
                           page=data,
                           data=data,
                           table_caption=table_caption,
                           title='mls-Maintenance',
                           copyright_year=year)


@encoder_tool_bp.route('/maintenance_add', methods=('GET', 'POST'))
@login_required
def maintenance_add():
    form = MaintenanceForm()
    choices = [item.plate_no for item in Vehicle.query.order_by('id').all()]
    form.plate_no.choices = remove_duplicate(choices)
    if form.validate_on_submit():
        try:
            if form.confirm.data:
                vehicle = db.session.execute(db.select(Vehicle).filter_by(plate_no=form.plate_no.data)).scalar()
                new_maintenance = Maintenance(
                    date=form.date.data,
                    amount=form.amount.data,
                    purpose=form.purpose.data.lower(),
                    plate_no=vehicle.plate_no,
                    vehicle_id=vehicle.id,
                    encoded_by=current_user.name,
                    encoded_on=date.today()
                )
                db.session.add(new_maintenance)
                db.session.commit()
                flash(f'Row #{new_maintenance.id} added successfully', 'success')
                return redirect(url_for('encoder_tool.maintenance'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('encoder_tool.maintenance_add'))

    year = date.today().year
    return render_template('encoder_tool/maintenance_add.html',
                           form=form,
                           title='mls-Maintenance_add',
                           copyright_year=year)


@encoder_tool_bp.route('/maintenance_edit/<int:maintenance_id>', methods=('GET', 'POST'))
@login_required
def maintenance_edit(maintenance_id):
    edit_maintenance = Maintenance.query.get(maintenance_id)
    # fill-up form
    edit_form = MaintenanceForm(
        date=edit_maintenance.date,
        amount=edit_maintenance.amount,
        purpose=edit_maintenance.purpose,
    )
    choices = [item.plate_no for item in Vehicle.query.order_by('id').all()]
    edit_form.plate_no.choices = remove_duplicate(choices)
    if edit_form.validate_on_submit():
        try:
            vehicle = db.session.execute(db.select(Vehicle).filter_by(plate_no=edit_form.plate_no.data)).scalar()
            if edit_form.confirm.data:
                edit_maintenance.date = edit_form.date.data
                edit_maintenance.amount = edit_form.amount.data
                edit_maintenance.purpose = edit_form.purpose.data
                edit_maintenance.plate_no = vehicle.plate_no
                edit_maintenance.vehicle_id = vehicle.id
                edit_maintenance.edited_by = current_user.name
                edit_maintenance.edited_on = date.today()
                db.session.commit()
                flash(f'Row #{edit_maintenance.id} edited successfully', 'success')
                return redirect(url_for('encoder_tool.maintenance'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not edited!', 'danger')
            return redirect(url_for('encoder_tool.maintenance_edit'))

    year = date.today().year
    return render_template('encoder_tool/maintenance_edit.html',
                           form=edit_form,
                           title='mls-Maintenance_edit',
                           copyright_year=year)


@encoder_tool_bp.route('/maintenance_delete/<int:maintenance_id>', methods=('GET', 'POST'))
@login_required
def maintenance_delete(maintenance_id):
    maintenance_to_delete = Maintenance.query.get(maintenance_id)
    if maintenance_to_delete.transaction_id:
        transaction_id = maintenance_to_delete.transaction_id
        flash(f'Cannot delete this maintenance. It is included in TRANSACTION#:{transaction_id}.', 'danger')
        return redirect(url_for('encoder_tool.dispatch'))

    if request.method == 'POST':
        if request.form.get('delete_button') == 'confirm':
            db.session.delete(maintenance_to_delete)
            db.session.commit()
            flash(f'Row #{maintenance_id} deleted successfully.', 'success')
            return redirect(url_for('encoder_tool.maintenance'))
        elif request.form.get('delete_button') == 'cancel':
            flash('Delete operation aborted.', 'info')
            return redirect(url_for('encoder_tool.maintenance'))

    year = date.today().year
    return render_template('encoder_tool/maintenance_delete.html',
                           maintenance_id=maintenance_id,
                           title='mls-Maintenance_delete',
                           copyright_year=year)


@encoder_tool_bp.route('/maintenance_view/<int:maintenance_id>', methods=('GET', 'POST'))
@login_required
def maintenance_view(maintenance_id):
    main_view = pd.read_sql_table('maintenance', db.engine, index_col='id')
    data_maintenance = main_view.loc[maintenance_id]
    year = date.today().year
    return render_template('encoder_tool/maintenance_view.html',
                           data=data_maintenance,
                           title='mls-Maintenance_view',
                           copyright_year=year)


@encoder_tool_bp.route('/dispatch', methods=('GET', 'POST'))
@login_required
def dispatch():
    table_row_per_page = 10
    form = FilterForm3()

    # form choices
    dispatch_query = db.session.execute(db.select(Dispatch)).scalars()
    choices_invoice_no = [item.invoice_no for item in dispatch_query if item.invoice_no is not None]
    choices_plate_no = [item.plate_no for item in dispatch_query if item.plate_no is not None]

    choices_plate_no.insert(0, '-all-')
    choices_plate_no.insert(1, '-none-')
    choices_invoice_no.insert(0, '-none-')
    choices_invoice_no.insert(1, '-all-')

    form.plate_no.choices = remove_duplicate(choices_plate_no)
    form.invoice_no.choices = remove_duplicate(choices_invoice_no)

    if form.validate_on_submit():
        # store form data to session variables
        session['dispatch_filter_from_'] = form.from_.data.isoformat()
        session['dispatch_filter_to_'] = form.to_.data.isoformat()
        session['dispatch_filter_invoice_no'] = form.invoice_no.data
        session['dispatch_filter_plate_no'] = form.plate_no.data
        session['dispatch_filtered'] = True
        return redirect(url_for('encoder_tool.dispatch'))

    elif session.get('dispatch_filtered'):
        # retrieve data from session variables
        val1 = date.fromisoformat(session.get('dispatch_filter_from_'))
        val2 = date.fromisoformat(session.get('dispatch_filter_to_'))
        val3 = session.get('dispatch_filter_invoice_no')
        val4 = session.get('dispatch_filter_plate_no')

        # pre-load filter values
        form = FilterForm3(
            from_=val1,
            to_=val2,
            invoice_no=val3,
            plate_no=val4,
        )

        # form choices
        dispatch_query = db.session.execute(db.select(Dispatch)).scalars()
        choices_invoice_no = [item.invoice_no for item in dispatch_query if item.invoice_no is not None]
        choices_plate_no = [item.plate_no for item in dispatch_query if item.plate_no is not None]

        choices_plate_no.insert(0, '-all-')
        choices_plate_no.insert(1, '-none-')
        choices_invoice_no.insert(0, '-none-')
        choices_invoice_no.insert(1, '-all-')

        form.plate_no.choices = remove_duplicate(choices_plate_no)
        form.invoice_no.choices = remove_duplicate(choices_invoice_no)

        # select data with filter value
        if val3 == '-none-':  # invoice no
            if val4 == '-all-':  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                    Dispatch.invoice_no == None,
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            elif val4 == '-none-':  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                    Dispatch.invoice_no == None,
                    Dispatch.vehicle_id == None
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            else:  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                    Dispatch.invoice_no == None,
                    Dispatch.plate_no == val4
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'

        elif val3 == '-all-':  # invoice no
            if val4 == '-all-':  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            elif val4 == '-none-':  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                    Dispatch.vehicle_id == None
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'
            else:  # plate no
                data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                    Dispatch.date.between(val1, val2),
                    Dispatch.plate_no == val4
                ), per_page=table_row_per_page)
                table_caption = f'page: {data.page} of {data.pages}'

        else:  # invoice no
            data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
                Dispatch.date.between(val1, val2),
                Dispatch.invoice_no == val3,
                Dispatch.plate_no == val4,
            ), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'

    else:
        data = db.paginate(db.select(Dispatch).order_by(desc('date')).filter(
        ), per_page=table_row_per_page)
        table_caption = f'page: {data.page} of {data.pages}'
    year = date.today().year
    return render_template('encoder_tool/dispatch.html',
                           form=form,
                           object=Dispatch,
                           page=data,
                           data=data,
                           table_caption=table_caption,
                           title='mls-Dispatch',
                           copyright_year=year)


@encoder_tool_bp.route('/dispatch_add', methods=('GET', 'POST'))
@login_required
def dispatch_add():
    form = DispatchForm()

    # form choices
    choices_destination = [(item.id, f'{item.destination}, {item.area} ({item.rate})')
                           for item in db.session.execute(db.select(Tariff)).scalars()]
    choices_plate_no = [(item.id, item.plate_no) for item in db.session.execute(db.select(Vehicle)).scalars()]
    choices_driver = [(item.id, f'{item.first_name.title()} {item.middle_name[0].title()}. {item.last_name.title()}')
                      for item in db.session.execute(db.select(Employee)).scalars()]
    choices_helper = [(item.id, f'{item.first_name.title()} {item.middle_name[0].title()}. {item.last_name.title()}')
                      for item in db.session.execute(db.select(Employee)).scalars()]

    form.destination.choices = remove_duplicate(choices_destination)
    form.plate_no.choices = remove_duplicate(choices_plate_no)
    form.driver.choices = remove_duplicate(choices_driver)
    form.helper.choices = remove_duplicate(choices_helper)

    if form.validate_on_submit():
        try:
            vehicle = db.get_or_404(Vehicle, form.plate_no.data)
            tariff = db.get_or_404(Tariff, form.destination.data)
            helper = db.get_or_404(Employee, form.helper.data)
            driver = db.get_or_404(Employee, form.driver.data)

            # rate adjustment base on wd_code
            wd_code = form.wd_code.data.lower()
            if wd_code == 'hol':
                rate = tariff.rate + driver.rate + helper.rate
            elif wd_code == 'sp':
                rate = tariff.rate + (0.3*driver.rate) + (0.3*helper.rate)
            elif wd_code == 'rd':
                rate = tariff.rate + (0.5*driver.rate) + (0.5*helper.rate)
            else:
                # wd_code == norm
                rate = tariff.rate

            new_dispatch = Dispatch(
                date=form.date.data,
                wd_code=wd_code,
                slip=form.slip.data,
                qty=form.qty.data,
                cbm=form.cbm.data,
                drops=form.drops.data,
                plate_no=vehicle.plate_no,
                destination=f'{tariff.destination}, {tariff.area}',
                rate=rate,
                helper=f'{helper.first_name.title()} {helper.middle_name[0].title()}. {helper.last_name.title()}',
                driver=f'{driver.first_name.title()} {driver.middle_name[0].title()}. {driver.last_name.title()}',
                vehicle_id=vehicle.id,
                tariff_id=tariff.id,

                encoded_by=current_user.name,
                encoded_on=date.today(),
            )
            db.session.add(new_dispatch)
            # update emp_table
            new_dispatch.employees.append(driver)
            new_dispatch.employees.append(helper)
            db.session.commit()
            flash(f'Row #{new_dispatch.id} added successfully', 'success')
            return redirect(url_for('encoder_tool.dispatch'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. Data not ADDED!', 'danger')
            return redirect(url_for('encoder_tool.dispatch_add'))

    year = date.today().year
    return render_template('encoder_tool/dispatch_add.html',
                           form=form,
                           title='mls-Dispatch_add',
                           copyright_year=year)


@encoder_tool_bp.route('/dispatch_edit/<int:dispatch_id>', methods=('GET', 'POST'))
@login_required
def dispatch_edit(dispatch_id):
    edit_dispatch = db.get_or_404(Dispatch, dispatch_id)

    # pre-load form
    edit_form = DispatchForm(
        date=edit_dispatch.date,
        wd_code=edit_dispatch.wd_code,
        slip=edit_dispatch.slip,
        destination=edit_dispatch.destination,
        qty=edit_dispatch.qty,
        cbm=edit_dispatch.cbm,
        drops=edit_dispatch.drops,
        plate_no=edit_dispatch.plate_no,
        driver=edit_dispatch.driver,
        helper=edit_dispatch.helper,
    )

    # form choices
    choices_destination = [(item.id, f'{item.destination}, {item.area} ({item.rate})')
                           for item in db.session.execute(db.select(Tariff)).scalars()]
    choices_plate_no = [(item.id, item.plate_no) for item in db.session.execute(db.select(Vehicle)).scalars()]
    choices_driver = [(item.id, f'{item.first_name.title()} {item.middle_name[0].title()}. {item.last_name.title()}')
                      for item in db.session.execute(db.select(Employee)).scalars()]
    choices_helper = [(item.id, f'{item.first_name.title()} {item.middle_name[0].title()}. {item.last_name.title()}')
                      for item in db.session.execute(db.select(Employee)).scalars()]

    edit_form.destination.choices = remove_duplicate(choices_destination)
    edit_form.plate_no.choices = remove_duplicate(choices_plate_no)
    edit_form.driver.choices = remove_duplicate(choices_driver)
    edit_form.helper.choices = remove_duplicate(choices_helper)

    if edit_form.validate_on_submit():
        try:
            vehicle = db.get_or_404(Vehicle, edit_form.plate_no.data)
            tariff = db.get_or_404(Tariff, edit_form.destination.data)
            helper = db.get_or_404(Employee, edit_form.helper.data)
            driver = db.get_or_404(Employee, edit_form.driver.data)

            edit_dispatch.date = edit_form.date.data
            edit_dispatch.wd_code = edit_form.wd_code.data.lower()
            edit_dispatch.slip = edit_form.slip.data
            edit_dispatch.qty = edit_form.qty.data
            edit_dispatch.cbm = edit_form.cbm.data
            edit_dispatch.drops = edit_form.drops.data
            edit_dispatch.plate_no = vehicle.plate_no
            edit_dispatch.destination = f'{tariff.destination}, {tariff.area}'
            edit_dispatch.rate = tariff.rate
            edit_dispatch.helper = f'{helper.first_name.title()} {helper.middle_name[0].title()}. {helper.last_name.title()}'
            edit_dispatch.driver = f'{driver.first_name.title()} {driver.middle_name[0].title()}. {driver.last_name.title()}'
            edit_dispatch.vehicle_id = vehicle.id
            edit_dispatch.tariff_id = tariff.id
            edit_dispatch.edited_by = current_user.name
            edit_dispatch.edited_on = date.today()

            edit_dispatch.employees.append(driver)
            edit_dispatch.employees.append(helper)

            db.session.commit()

            flash(f'Row #{edit_dispatch.id} edited successfully', 'success')
            return redirect(url_for('encoder_tool.dispatch'))

        except exc.IntegrityError as e:
            flash(f'{e.__dict__["orig"]}. EDIT operation fail!', 'warning')
            return redirect(url_for('encoder_tool.dispatch_add'))

    year = date.today().year
    return render_template('encoder_tool/dispatch_edit.html',
                           form=edit_form,
                           title='mls-Dispatch_edit',
                           copyright_year=year)


@encoder_tool_bp.route('/dispatch_delete/<int:dispatch_id>', methods=('GET', 'POST'))
@login_required
def dispatch_delete(dispatch_id):
    disp = db.get_or_404(Dispatch, dispatch_id)
    if disp.invoice_id or disp.payroll_id:
        inv_no = disp.invoice_no
        payroll_id = disp.payroll_id
        flash(f'Cannot delete this dispatch. It is included in PAYROLL#:{payroll_id} and INVOICE: {inv_no}', 'danger')
        return redirect(url_for('encoder_tool.dispatch'))
    else:
        if request.method == 'POST':
            if request.form.get('delete_button') == 'confirm':
                db.session.delete(disp)
                db.session.commit()
                flash(f'Row #{dispatch_id} deleted successfully.', 'success')
                return redirect(url_for('encoder_tool.dispatch'))
            elif request.form.get('delete_button') == 'cancel':
                flash('Delete operation aborted.', 'info')
                return redirect(url_for('encoder_tool.dispatch'))

    year = date.today().year
    return render_template('encoder_tool/dispatch_delete.html',
                           dispatch_id=dispatch_id,
                           title='mls-Dispatch_delete',
                           copyright_year=year)


@encoder_tool_bp.route('/dispatch_view/<int:dispatch_id>', methods=('GET', 'POST'))
@login_required
def dispatch_view(dispatch_id):
    main_view = pd.read_sql_table('dispatch', db.engine, index_col='id')
    data_dispatch = main_view.loc[dispatch_id]
    year = date.today().year
    return render_template('encoder_tool/dispatch_view.html',
                           data=data_dispatch,
                           title='mls-Dispatch_view',
                           copyright_year=year)
