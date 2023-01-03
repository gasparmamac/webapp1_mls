import os
from dotenv import load_dotenv

# path to instance folder
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# postgresql - sqlalchemy issue solution
uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri:
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)


class Config(object):
    # default setting
    SECRET_KEY = os.environ.get('SECRET_KEY')
    INVOICE_FOLDER = basedir

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
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False

    # sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = uri

    # SQLALCHEMY_DATABASE_URI = os.environ.get(f"{uri}", os.path.join(f"sqlite:////{basedir}", "mls.db"))
