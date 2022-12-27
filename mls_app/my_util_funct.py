from fpdf import FPDF
from flask_login import current_user
import os
from flask import current_app


# remove duplicate items from a list
def remove_duplicate(list_with_duplicate):
    return list(dict.fromkeys(list_with_duplicate))


# computes the total working day and the total amount of payroll
def compute_emp_payroll(employees_query):
    disp_indexes = []
    payroll_list = []
    total = 0

    for emp in employees_query:
        emp_name = f'{emp.first_name.title()} {emp.middle_name[0].title()}. {emp.last_name.title()}'
        # sum-up wd_code
        norm = 0
        hol = 0
        sp_hol = 0
        rd = 0

        for disp in emp.dispatches:
            if disp.payroll_id is None:
                disp_indexes.append(disp.id)
                if disp.wd_code == 'norm':
                    norm += 1
                elif disp.wd_code == 'hol':
                    hol += 1
                elif disp.wd_code == 'sp':
                    sp_hol += 1
                elif disp.wd_code == 'rd':
                    rd += 1

            # compute for wages
        total_wd = norm + (2 * hol) + (1.3 * sp_hol) + (1.5 * rd)
        rate = emp.rate
        allowance = (emp.allowance * (norm + hol + sp_hol + rd))
        gross = round((total_wd * rate) + allowance, 2)
        new_payroll_entry = [emp.id, emp_name, norm, hol, sp_hol, rd, total_wd, rate, allowance, gross]

        # update return values
        total += gross
        payroll_list.append(new_payroll_entry)

    return payroll_list, round(total, 2)


# find max date
def max_date(invoice_query):
    date_list =[i.date for i in invoice_query.dispatches]
    return max(date_list)


# find min date
def min_date(invoice_query):
    date_list = [i.date for i in invoice_query.dispatches]
    return min(date_list)


def qty_total(invoice_query):
    qty = 0
    for i in invoice_query.dispatches:
        qty += i.qty
    return qty


def cbm_total(invoice_query):
    cbm = 0
    for i in invoice_query.dispatches:
        cbm += i.cbm
    return cbm


def drops_total(invoice_query):
    drops = 0
    for i in invoice_query.dispatches:
        drops += i.drops
    return drops


def rate_total(invoice_query):
    rate = 0
    for i in invoice_query.dispatches:
        rate += i.rate
    return rate


def create_pdf(ctrl_no, header, address, landline, cellphone,
               date_, start_date, end_date, sorted_dict,
               qty_ttl, cbm_ttl, drops_ttl, rate_ttl,
               adjustment, adj_remarks, amount_due, amount_in_words, owner):
    """PDF printing"""
    # create object
    pdf = FPDF('P', 'mm', 'A4')
    # get total page numbers
    pdf.alias_nb_pages()
    # metadata
    pdf.set_title(ctrl_no)
    pdf.set_author(f'{current_user.name}')
    # set auto page break
    pdf.set_auto_page_break(auto=True, margin=15)
    # add page
    pdf.add_page()

    # Company
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, header, ln=1, border=0)
    # Address
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, address, ln=1, border=0)
    pdf.cell(0, 5, f'Tel#: {landline} / Cellphone#: {cellphone}', ln=1, border=0)

    # line break
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(128, 128, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'INVOICE', border=0, ln=1, align='C', fill=1)

    # bill to
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(15, 6, 'Bill to: ', ln=0, border=0)
    # customer
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(115, 6, 'LBC Express Inc.', ln=0, border=0)
    # invoice no
    pdf.set_font('helvetica', '', 8)
    pdf.cell(20, 6, 'Invoice no: ', border=0)
    # actual invoice
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(25, 6, ctrl_no, ln=1, border=0)

    # below customer line
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(15, 6, 'Address: ', ln=0, border=0)
    pdf.cell(115, 6, "Km. 6, JP Laurel Ave., Lanang, Davao City", ln=0, border=0)
    pdf.cell(20, 6, "Invoice Date: ", ln=0, border=0)
    pdf.cell(25, 6, date_, ln=1, border=0)

    # line break
    pdf.ln(10)

    # dispatch from - to
    pdf.cell(10, 6, "From: ", ln=0, border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(25, 6, start_date, ln=0, border=0)
    pdf.set_font('helvetica', '', 8)
    pdf.cell(10, 6, "To: ", ln=0, border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(110, 6, end_date, border=0)
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(25, 6, 'wd_code: hol*, sp**, rd***', ln=1)

    # header
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(12, 6, '#', border=1)
    pdf.cell(25, 6, 'Disp_date', border=1)
    pdf.cell(20, 6, 'Slip#', border=1)
    pdf.cell(20, 6, 'Plate#', border=1)
    pdf.cell(53, 6, 'Destination', border=1)
    pdf.cell(12, 6, 'Qty', border=1)
    pdf.cell(12, 6, 'Cbm', border=1)
    pdf.cell(12, 6, 'Drop/s', border=1)
    pdf.cell(25, 6, 'Amount', border=1, ln=1)

    # data
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)

    # table
    for k, disp in enumerate(sorted_dict.values(), start=1):
        pdf.cell(12, 6, str(k), border=1)
        if disp.get('wd_code') == 'hol':
            pdf.cell(25, 6, f"{disp.get('date')}*", border=1)
        elif disp.get('wd_code') == 'sp':
            pdf.cell(25, 6, f"{disp.get('date')}**", border=1)
        elif disp.get('wd_code') == 'rd':
            pdf.cell(25, 6, f"{disp.get('date')}***", border=1)
        else:
            pdf.cell(25, 6, f"{disp.get('date')}", border=1)
        pdf.cell(20, 6, disp.get('slip'), border=1)
        pdf.cell(20, 6, disp.get('plate_no'), border=1)
        pdf.cell(53, 6, disp.get('destination'), border=1)
        pdf.cell(12, 6, str(disp.get('cbm')), border=1)
        pdf.cell(12, 6, str(disp.get('qty')), border=1)
        pdf.cell(12, 6, str(disp.get('drops')), border=1)
        pdf.cell(25, 6, "Php {:,.2f}".format(disp.get('rate')), border=1, ln=1)

    # summary
    pdf.set_text_color(0, 0, 0)
    pdf.cell(130, 6, 'Total', border=1)
    pdf.cell(12, 6, str(qty_ttl), border=1)
    pdf.cell(12, 6, str(cbm_ttl), border=1)
    pdf.cell(12, 6, str(drops_ttl), border=1)
    pdf.cell(25, 6, "Php {:,.2f}".format(rate_ttl), border=1, ln=1)

    # adjustment
    pdf.set_font('helvetica', 'I', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(30, 6, 'Adjustment (if any):')
    if adjustment:
        pdf.cell(136, 6, adj_remarks)
        pdf.cell(25, 6, "Php {:,.2f}".format(adjustment), ln=1)
    else:
        pdf.cell(136, 6, 'None')
        pdf.cell(25, 6, 'None', ln=1)

    # total
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(130, 6)
    pdf.cell(36, 6, 'Amount due:')
    pdf.cell(25, 6, "Php {:,.2f}".format(amount_due), ln=1)

    # amount in words
    pdf.set_font('helvetica', '', 8)
    pdf.cell(40, 6, 'Amount due in words:', ln=1)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 6, amount_in_words, ln=1)

    # payable to
    pdf.ln(1)
    pdf.set_font('helvetica', 'I', 8)
    pdf.cell(45, 6, 'Please make all checks payable to:', ln=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 6, owner, ln=1)

    # approve by (delete later)
    pdf.ln(10)
    pdf.set_font('helvetica', '', 8)
    pdf.cell(130, 6, 'Checked and Approved by:', ln=0, border=0)
    pdf.cell(35, 6, 'Received by:', ln=1, border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(130, 6, '____________________', ln=0)
    pdf.cell(130, 6, '____________________', ln=1)
    pdf.set_font('helvetica', 'I', 8)
    pdf.cell(130, 1, '(Name / Signature / Date)')
    pdf.cell(130, 1, '(Name / Signature / Date)', ln=1)

    # term of payment
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, '*** Terms of Payment ***', border=0, ln=1, align='C')
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'The DUE DATE is thirty (30) calendar days from the received-date of this invoice.', border=0,
             ln=1, align='C')
    pdf.cell(0, 6, 'Kindly SETTLE this invoice ON or BEFORE that day.', border=0,
             ln=1, align='C')

    filename = f"{ctrl_no}.pdf"
    directory = current_app.config['INVOICE_FOLDER']
    path = os.path.join(directory, filename)

    pdf.output(name=path)

    return filename, directory, path
