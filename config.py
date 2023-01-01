import os
from dotenv import load_dotenv

# path to instance folder
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # invoice related variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    INVOICE_FOLDER = os.path.join(f"{basedir}/mls_app/static", 'Invoices')

    # recaptcha
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')


class DevelopmentConfig(Config):
    # default variables
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True

    # sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = os.path.join(f"sqlite:////{basedir}", "mls.db")


class ProductionConfig(Config):
    # default variables
    FLASK_ENV = 'develop'
    DEBUG = False
    TESTING = False

    # sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////mls.db)'



