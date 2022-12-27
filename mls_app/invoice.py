import os
from datetime import date
from pprint import pprint

import pandas as pd
from num2words import num2words
from flask import Blueprint, render_template, redirect, url_for, \
    session, request, flash, send_from_directory

from flask_login import login_required

from sqlalchemy import desc

from .db import *
from .forms import *
from .my_util_funct import *

invoicing_bp = Blueprint('invoice', __name__, url_prefix='/invoice')


# template filter for preferred date format
@invoicing_bp.app_template_filter('my_date_format')
def my_date_format(value, my_format='%Y-%m-%d'):
    return value.strftime(my_format)


# peso format
@invoicing_bp.app_template_filter('peso_format')
def peso_format(value):
    return "₱{:,.2f}".format(value)


@invoicing_bp.route('/invoice', methods=('GET', 'POST'))
@login_required
def invoice():
    table_row_per_page = 10
    form = FilterInvoiceForm()

    if form.validate_on_submit():
        # store form data to session variables
        session['invoice_filter_status'] = form.status.data
        session['invoice_filtered'] = True
        return redirect(url_for('invoice.invoice'))

    elif session.get('invoice_filtered'):
        val = session.get('invoice_filter_status')
        form = FilterInvoiceForm(
            status=val,
        )
        if val == 'paid':
            data = db.paginate(db.select(Invoice).order_by(desc('date')).filter(
                Invoice.or_no != None
            ), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'

        elif val == 'unpaid':
            data = db.paginate(db.select(Invoice).order_by(desc('date')).filter(
                Invoice.or_no == None
            ), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'

        elif val == 'all':
            data = db.paginate(db.select(Invoice).order_by(desc('date')), per_page=table_row_per_page)
            table_caption = f'page: {data.page} of {data.pages}'
    else:
        data = db.paginate(db.select(Invoice).order_by(desc('date')).filter(
            Invoice.or_no == None
        ), per_page=table_row_per_page)
        table_caption = f'page: {data.page} of {data.pages}'

    no_invoice = pd.read_sql_query(db.select(Dispatch).order_by(desc('date')).filter(
        Dispatch.invoice_no == None
    ), con=db.engine)

    for i in data:
        pprint(i.date)
    disp_count = no_invoice['slip'].count()
    year = date.today().year
    return render_template('invoice/invoice.html',
                           title='Invoicing_view',
                           object=Invoice,
                           form=form,
                           data=data,
                           table_caption=table_caption,
                           disp_count=disp_count,
                           copyright_year=year)


@invoicing_bp.route('/invoice_create_s1', methods=('GET', 'POST'))
@login_required
def invoice_create_s1():
    form = CreateInvoiceForm()
    form.template.choices = [
        ('', '-select-'),
        (1, 'Mamac Logistics Services'),
        (2, 'Nimrod Logistics Services')
    ]
    if request.method == 'POST':
        # get dispatch id
        disp_id = request.form.get('dispatch_id')
        session['prev_items'] = len(session['holder_dict']) + len(session['disp_dict'])

        # move dispatch to holding dictionary
        if request.form.get('action') == 'add':
            # move selected disp to holder dictionary
            try:
                temp_dict = session['disp_dict'][disp_id]
                session['holder_dict'][disp_id] = temp_dict
                session['disp_dict'].pop(disp_id)

                # sort holder dict
                res = sorted(session['holder_dict'].items(), key=lambda x: x[1]['plate_no'])
                session['holder_dict'] = {k: v for k, v in res}

                # compute for the total amount
                session['holder_dict_amount'] = 0
                for val in session['holder_dict'].values():
                    session['holder_dict_amount'] += val['rate']

                # display information on screen
                flash(
                    f'Disp# {request.form.get("dispatch_id")} moved successfully! Total: {session["holder_dict_amount"]}')

            except KeyError:
                return redirect(url_for('invoice.invoice_create_s1'))

        # return dispatch to dispatch dictionary
        if request.form.get('action') == 'remove':
            # return selected disp to disp dict
            try:
                temp_dict = session['holder_dict'][disp_id]
                session['disp_dict'][disp_id] = temp_dict
                session['holder_dict'].pop(disp_id)

                # sort disp dict
                res = sorted(session['disp_dict'].items(), key=lambda x: x[1]['plate_no'])
                session['disp_dict'] = {k: v for k, v in res}

                # compute for the total amount
                session['holder_dict_amount'] = 0
                for val in session['holder_dict'].values():
                    session['holder_dict_amount'] += val['rate']

                flash(f'Disp# {request.form.get("dispatch_id")} removed from holding list.', 'danger')
            except KeyError:
                return redirect(url_for('invoice.invoice_create'))

        # display summary of the invoice to be created
        if request.form.get('next'):
            try:
                form2 = CreateInvoiceConfirm()
                session['invoice_template'] = form.template.data
                session['invoice_adjustment'] = form.adjustment.data
                session['invoice_remarks'] = form.remarks.data

                # compute for final invoice amount
                if session['invoice_adjustment']:
                    session['final_amount'] = session['holder_dict_amount'] + session['invoice_adjustment']
                else:
                    session['final_amount'] = session['holder_dict_amount']

                holder_df = pd.DataFrame.from_dict(session['holder_dict']).T
                holder_df = holder_df.groupby('plate_no').agg({'slip': 'count', 'rate': 'sum'})
            except KeyError:
                return redirect(url_for('invoice.invoice_create'))

            return render_template('invoice/invoice_create_confirmation.html',
                                   form=form2,
                                   data=holder_df)

        # go back to create invoice
        if request.form.get('back'):
            return redirect('invoice_create_s1')

        # create invoice
        if request.form.get('confirm'):
            try:
                # get template value
                template_val = int(session['invoice_template'])

                # create ctrl_no
                if template_val == 1:
                    initial = 'A'

                if template_val == 2:
                    initial = 'N'

                # check previous invoice template record
                inv_exist = db.session.execute(db.select(Invoice).filter(
                    Invoice.template == template_val
                )).scalar()

                # if no previous invoice
                if not inv_exist:
                    series = 1
                    ctrl_no = f'{date.today().year}-{initial}-{series}'

                # if there is an existing invoice
                else:
                    last_invoice = db.session.execute(db.select(Invoice).order_by(desc('ctrl_no')).filter(
                        Invoice.template == template_val
                    )).scalar()

                    pprint(last_invoice)
                    split_old_ctrl_no = last_invoice.ctrl_no.split('-')
                    series = int(split_old_ctrl_no[2]) + 1
                    ctrl_no = f'{date.today().year}-{initial}-{series}'

                if session['invoice_adjustment']:
                    adj = round(session['invoice_adjustment'], 2)
                else:
                    adj = 0
                # create new invoice
                new_invoice = Invoice(
                    template=template_val,
                    date=date.today(),
                    ctrl_no=ctrl_no,
                    amount=round(session['final_amount'], 2),
                    remarks=session['invoice_remarks'],
                    adjustment=adj,
                    generated_by=current_user.name,
                    generated_on=date.today()
                )
                db.session.add(new_invoice)

                # update invoice_id to the holder dict dispatch items
                for k, v in session['holder_dict'].items():
                    disp_id = int(k)
                    disp = db.get_or_404(Dispatch, disp_id)
                    disp.invoice = new_invoice
                    disp.invoice_no = ctrl_no
                    disp.invoice_date = date.today()

                # commit changes
                db.session.commit()

                # display info on screen
                flash(f'Invoice {ctrl_no} successfully added!')
            except KeyError:
                return redirect(url_for('invoice.invoice_create'))

            # pop all session variables
            if 'holder_dict' in session:
                session.pop('holder_dict', None)
            if 'disp_dict' in session:
                session.pop('disp_dict', None)
            if 'holder_dict_amount' in session:
                session.pop('holder_dict_amount', None)
            if 'invoice_template' in session:
                session.pop('invoice_template', None)
            if 'invoice_adjustment' in session:
                session.pop('invoice_adjustment', None)
            if 'invoice_remarks' in session:
                session.pop('invoice_remarks', None)
            if 'final_amount' in session:
                session.pop('final_amount', None)
            if 'prev_items' in session:
                session.pop('prev_items', None)

            return redirect(url_for('invoice.invoice'))

    elif request.method == 'GET':
        # get dispatch data from the database
        disp_df = pd.read_sql_query(db.select(Dispatch).order_by('plate_no').filter(
            Dispatch.invoice_no == None
        ),
            con=db.engine,
            index_col='id',
            parse_dates='date',
        )
        db_items = len(disp_df)

        # first entry or invoicing is not active
        if 'holder_dict' not in session or not session['holder_dict']:
            # convert to dictionary format and save to session
            session['disp_dict'] = disp_df.to_dict('index')
            session['holder_dict'] = {}

        # when there are changes on the dispatch db
        elif db_items != session['prev_items']:
            # update dispatch dictionary in session
            temp_dict = disp_df.to_dict('index')

            # remove items that is present in the holder dict
            session['disp_dict'] = {k: v for k, v in temp_dict.items() if str(k) not in session['holder_dict'].keys()}

    table_caption = 'end-of-table'
    year = date.today().year
    return render_template('invoice/invoice_create_s1.html',
                           title='Invoice_create',
                           form=form,
                           table_caption=table_caption,
                           copyright_year=year
                           )


@invoicing_bp.route('/invoice_view/<int:invoice_id>', methods=('GET', 'POST'))
@login_required
def invoice_print(invoice_id):
    data = db.get_or_404(Invoice, invoice_id)
    sorted_dispatch_list = sorted(data.dispatches, key=lambda x: x.plate_no)

    # convert to dictionary for serialization
    sorted_disp_dict = {k: dict(date=v.date.isoformat(), slip=v.slip, plate_no=v.plate_no, destination=v.destination,
                                qty=v.qty, wd_code=v.wd_code, cbm=v.cbm, drops=v.drops, rate=v.rate)
                        for k, v in enumerate(sorted_dispatch_list, start=1)}

    # header
    if data.template == 1:  # mine
        header = 'Mamac Logistics Services'
        address = 'Lot 9, Block 3, Lulu Village, Brgy. R. Castillo Agdao, Davao City, Davao del Sur Philippines 8000'
        cellphone = '0917-5143642'
        landline = '(032) 234-2813'
    elif data.template == 2:  # kuya eloy's
        header = 'Nimrod Logistics Services'
        address = 'Lot 9, Block 3, Lulu Village, Brgy. R. Castillo Agdao, Davao City, Davao del Sur Philippines 8000'
        cellphone = '0923-6003604 /0992-3063050'
        landline = '(082 ) 272-4159'

    ctrl_no = data.ctrl_no
    date_ = data.date.isoformat()

    start_date = min_date(data).isoformat()
    end_date = max_date(data).isoformat()

    # table
    sorted_dict = sorted_disp_dict

    # summary
    qty_ttl = qty_total(data)
    cbm_ttl = cbm_total(data)
    drops_ttl = drops_total(data)
    rate_ttl = round(rate_total(data), 2)

    adjustment = data.adjustment
    adj_remarks = data.remarks

    amount_due = round(data.amount, 2)
    amount_due = amount_due

    # footer
    amount_in_words = num2words(amount_due).title() + ' Pesos'

    if data.template == 1:
        owner = 'Mamac Logistics Services / Mr. Gaspar Q. Mamac'
    elif data.template == 2:
        owner = 'Mr. Nimrod Q. Mamac'

    # create pdf copy
    filename, directory, path = create_pdf(ctrl_no, header, address, landline, cellphone, date_, start_date, end_date,
                                           sorted_dict, qty_ttl, cbm_ttl, drops_ttl, rate_ttl, adjustment, adj_remarks,
                                           amount_due, amount_in_words, owner)

    # return send_file(path, filename, as_attachment=False) # this also work
    return send_from_directory(directory=directory, path=filename, as_attachment=False)


@invoicing_bp.route('/invoice_edit/<int:invoice_id>', methods=('GET', 'POST'))
@login_required
def invoice_edit(invoice_id):
    inv = db.get_or_404(Invoice, invoice_id)
    form = InvoiceEditForm()

    if form.validate_on_submit():
        inv.or_no = form.or_no.data
        inv.amount_paid = form.amount_paid.data
        db.session.commit()
        flash(f"Invoice {inv.ctrl_no} successfully edited!", "success")
        return redirect(url_for('invoice.invoice'))
    year = date.today().year
    return render_template('invoice/invoice_edit.html',
                           title='Invoice_edit',
                           inv=inv,
                           form=form,
                           copyright_year=year
                           )
