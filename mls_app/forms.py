from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, SubmitField, DateField, TextAreaField, IntegerField, FloatField, \
    HiddenField, SelectField
from wtforms.validators import InputRequired, Email, EqualTo, Length, Optional, ValidationError


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    user_type = SelectField('User type', choices=['', 'Admin', 'Encoder', 'Driver', 'Courier'],
                            validators=[InputRequired()])
    email = StringField('Email', validators=[Email()])
    confirm_email = StringField('Confirm email', validators=[EqualTo('email')])
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm password', validators=[EqualTo('password')])
    confirm = SubmitField('Confirm')
    recaptcha = RecaptchaField()


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    confirm = SubmitField('Confirm')
    recaptcha = RecaptchaField()


class DispatchForm(FlaskForm):
    # dispatch
    date = DateField('Date', validators=[InputRequired()])
    wd_code = SelectField('WD Code', choices=['norm', 'hol', 'sp', 'rd'])
    slip = StringField('Disp. slip no.', validators=[InputRequired()])
    destination = SelectField('Destination', validators=[InputRequired()])
    qty = IntegerField('Qty.', validators=[InputRequired()])
    cbm = FloatField('Cbm', validators=[InputRequired()])
    drops = IntegerField('Drops', validators=[InputRequired()])
    plate_no = SelectField('Plate_no', validators=[InputRequired()])
    odo_start = IntegerField('Odo_start', render_kw={'placeholder': 'before dispatch atLBC'})
    odo_end = IntegerField('Odo_end', render_kw={'placeholder': 'after dispatch at LBC'})
    # unit
    driver = SelectField('Driver', validators=[InputRequired()])
    helper = SelectField('Helper', validators=[InputRequired()])

    def validate_helper(self, field):
        if field.data == self.driver.data:
            raise ValidationError('The helper must NOT be the same as the driver')
    confirm = SubmitField('Confirm')


class EmployeeForm(FlaskForm):
    # personal data
    id = HiddenField('emp_id')
    first_name = StringField('First name', validators=[InputRequired()])
    middle_name = StringField('Middle name', validators=[InputRequired()])
    last_name = StringField('Last name', validators=[InputRequired()])
    birthday = DateField('Birthday', validators=[InputRequired()])
    # contact detail
    mobile_no = StringField('Mobile no.', validators=[Length(min=11, max=11)])
    sss = StringField('SSS no', validators=[Optional()])
    phil_health = StringField('Phil-health', validators=[Optional()])
    pag_ibig = StringField('Pag-ibig', validators=[Optional()])
    # payroll data
    status = SelectField('Status', choices=['Extra', 'Contractual', 'Probationary', 'Regular'])
    rate = FloatField('Rate', validators=[InputRequired()])
    allowance = FloatField('Allowance', validators=[InputRequired()])
    confirm = SubmitField('Confirm')


class TariffForm(FlaskForm):
    area = StringField('Area', validators=[InputRequired()])
    destination = StringField('Destination', validators=[InputRequired()])
    km = FloatField('Km', validators=[InputRequired()])
    vehicle_model = SelectField('Vehicle model', validators=[InputRequired()])
    rate = FloatField('Rate', validators=[InputRequired()])
    confirm = SubmitField('Confirm')


class VehicleForm(FlaskForm):
    maker = StringField('Maker', validators=[InputRequired()])
    model = SelectField('Vehicle model', choices=['', 'L300', 'carry_uv', '6w', 'multicab'],
                        validators=[InputRequired()])
    year = StringField('Year', validators=[InputRequired()])
    plate_no = StringField('Plate no', validators=[InputRequired()])
    last_registration = DateField('Registered', validators=[InputRequired()])
    odo = IntegerField('Odo', validators=[InputRequired()])
    odo_updated = DateField('Odo taken', validators=[InputRequired()])
    confirm = SubmitField('Confirm')


class ExpenseForm(FlaskForm):
    date = DateField('Date', validators=[InputRequired()])
    amount = FloatField('Amount', validators=[InputRequired()])
    purpose = TextAreaField('Purpose', validators=[InputRequired()])
    confirm = SubmitField('Confirm')


class MaintenanceForm(FlaskForm):
    date = DateField('Date', validators=[InputRequired()])
    plate_no = SelectField('Plate_no', validators=[InputRequired()])
    amount = FloatField('Amount', validators=[InputRequired()])
    purpose = TextAreaField('Purpose', validators=[InputRequired()])
    confirm = SubmitField('Confirm')


class TransactionForm(FlaskForm):
    remarks = TextAreaField('Remarks', validators=[InputRequired()], description='Up to 200 characters')
    proceed = SubmitField('Proceed')
    cancel = SubmitField('Cancel')


# utility forms
class FilterForm1(FlaskForm):
    from_ = DateField('From:', validators=[InputRequired()])
    to_ = DateField('To:', validators=[InputRequired()])
    vehicle = SelectField('Vehicle:', validate_choice=False)
    transaction = SelectField('Transaction:')
    select = SubmitField('Apply filter')


class FilterForm2(FlaskForm):
    from_ = DateField('From:', validators=[InputRequired()])
    to_ = DateField('To:', validators=[InputRequired()])
    transaction = SelectField('Transaction:')
    select = SubmitField('Apply filter')


class FilterForm3(FlaskForm):
    from_ = DateField('From:', validators=[InputRequired()])
    to_ = DateField('To:', validators=[InputRequired()])
    invoice_no = SelectField('Invoice_no:')
    plate_no = SelectField('Plate_no:')
    select = SubmitField('Apply filter')


class FilterInvoiceForm(FlaskForm):
    status = SelectField('Filter:', choices=['unpaid', 'paid', 'all'])
    select = SubmitField('Apply filter')


class CreateInvoiceForm(FlaskForm):
    template = SelectField('Select template', validators=[InputRequired()])
    adjustment = FloatField('Invoice amount adjustment', description='If any (optional)',
                            render_kw={'placeholder': 0.0})
    remarks = TextAreaField('Remarks', validators=[Length(max=200)], description='200 character max')
    next = SubmitField('Next')


class CreateInvoiceConfirm(FlaskForm):
    confirm = SubmitField('Confirm')
    back = SubmitField('Back')


class InvoiceEditForm(FlaskForm):
    or_no = StringField('OR#', validators=[InputRequired()])
    amount_paid = FloatField('Amount paid', validators=[InputRequired()])
    submit = SubmitField('Submit')


class ForgetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    user_type = StringField('User type', validators=[InputRequired()])
    submit = SubmitField('Submit')
    recaptcha = RecaptchaField()


class UpdatePasswordForm(FlaskForm):
    user_id = HiddenField(validators=[InputRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm password', validators=[EqualTo('password')])
    update = SubmitField('Submit')
    recaptcha = RecaptchaField()
