from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

"""Helper Tables"""
emp_dispatch = db.Table('emp_dispatch',
                        db.Column('emp_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True),
                        db.Column('disp_id', db.Integer, db.ForeignKey('dispatch.id'), primary_key=True)
                        )

emp_payroll = db.Table('emp_payroll',
                       db.Column('emp_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True),
                       db.Column('payroll_id', db.Integer, db.ForeignKey('payroll.id'), primary_key=True)
                       )

"""First layer databases"""


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data
    name = db.Column(db.String(50), unique=False, nullable=False)
    user_type = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), primary_key=False, unique=False, nullable=False)

    # default data
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    encoded_by = db.Column(db.String(50), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)


class Expense(db.Model):
    __tablename__ = 'expenses'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)
    purpose = db.Column(db.String(250), nullable=False)

    """relationship"""
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.String(200))

    """relationship"""
    expenses = db.relationship('Expense', backref='transaction', lazy=True)
    maintenances = db.relationship('Maintenance', backref='transaction', lazy=True)
    payrolls = db.relationship('Payroll', backref='transaction', lazy=True)
    invoices = db.relationship('Invoice', backref='transaction', lazy=True)

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)
    purpose = db.Column(db.String(250), nullable=False)
    plate_no = db.Column(db.String(40), nullable=False)

    """relationships"""
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Payroll(db.Model):
    __tablename__ = 'payroll'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)

    """relationship"""
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    dispatches = db.relationship('Dispatch', backref='payroll', lazy=True)
    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Invoice(db.Model, UserMixin):
    __tablename__ = 'invoice'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data
    template = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, index=False, unique=False, nullable=False)
    ctrl_no = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)
    or_no = db.Column(db.Integer, nullable=True)
    amount_paid = db.Column(db.Float(precision=2))
    remarks = db.Column(db.String(200))
    adjustment = db.Column(db.Float(precision=2))

    """relationship"""
    dispatches = db.relationship('Dispatch', backref='invoice', lazy=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)

    # default data
    generated_by = db.Column(db.String(40), unique=False, nullable=False)
    generated_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    # default data
    id = db.Column(db.Integer, primary_key=True)
    maker = db.Column(db.String(50), unique=False, nullable=False)
    model = db.Column(db.String(50), unique=False, nullable=False)
    year = db.Column(db.String, unique=False, nullable=False)
    plate_no = db.Column(db.String(10), unique=True, nullable=False)
    last_registration = db.Column(db.Date, nullable=False)
    odo = db.Column(db.Integer, nullable=False)
    odo_updated = db.Column(db.Date, nullable=False)

    """relationships"""
    dispatches = db.relationship('Dispatch', backref='vehicle', lazy=True)
    maintenances = db.relationship('Maintenance', backref='vehicle', lazy=True)

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Tariff(db.Model):
    __tablename__ = 'tariff'
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    km = db.Column(db.Integer, nullable=False)
    vehicle_model = db.Column(db.String, nullable=False)
    rate = db.Column(db.Float(precision=2), nullable=False)

    """relationship"""
    dispatches = db.relationship('Dispatch', backref='tariff', lazy=True)

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Dispatch(db.Model, UserMixin):
    __tablename__ = 'dispatch'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # important data: dispatch
    date = db.Column(db.Date, unique=False, nullable=False)
    wd_code = db.Column(db.String(50), nullable=False)
    slip = db.Column(db.String(50), unique=True, nullable=False)
    qty = db.Column(db.Integer, unique=False, nullable=False)
    cbm = db.Column(db.Float(precision=1), unique=False, nullable=False)
    drops = db.Column(db.Integer, unique=False, nullable=False)
    plate_no = db.Column(db.String(40), nullable=False,)
    destination = db.Column(db.String(200), nullable=False)
    rate = db.Column(db.Float(precision=2), nullable=False)
    helper = db.Column(db.String(150), nullable=False)
    driver = db.Column(db.String(150), nullable=False)
    invoice_no = db.Column(db.String(40), nullable=True)
    invoice_date = db.Column(db.Date, nullable=True)
    odo_start = db.Column(db.Integer)
    odo_end = db.Column(db.Integer)

    """relationship"""
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariff.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)

    employees = db.relationship('Employee', secondary='emp_dispatch', backref='dispatches')

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)


class Employee(db.Model):
    __tablename__ = 'employee'
    # default data
    id = db.Column(db.Integer, primary_key=True)

    # personal data
    first_name = db.Column(db.String(50), unique=False, nullable=False)
    middle_name = db.Column(db.String(50), unique=False, nullable=False)
    last_name = db.Column(db.String(50), unique=False, nullable=False)
    birthday = db.Column(db.Date, unique=False, nullable=False)

    # contact data
    mobile_no = db.Column(db.String(11), unique=False, nullable=False)
    sss = db.Column(db.String(20), unique=True, nullable=True)
    phil_health = db.Column(db.String(20), unique=True, nullable=True)
    pag_ibig = db.Column(db.String(20), unique=True, nullable=True)

    # payroll data
    status = db.Column(db.String(20), unique=False, nullable=False)
    rate = db.Column(db.Float(precision=2), unique=False, nullable=False)
    allowance = db.Column(db.Float(precision=2), unique=False, nullable=False)

    """relationships"""
    payrolls = db.relationship('Payroll', secondary='emp_payroll', lazy='subquery',
                               backref=db.backref('employees', lazy=True))

    # default data
    encoded_by = db.Column(db.String(40), unique=False, nullable=False)
    encoded_on = db.Column(db.Date, unique=False, nullable=False)
    edited_by = db.Column(db.String(50))
    edited_on = db.Column(db.Date)

