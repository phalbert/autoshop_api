"""Default configuration

Use env var to override
"""
import os
from environs import Env

env = Env()
env.read_env()


def get_db_url():
    try:
        return env.str("DATABASE_URL")
    except Exception:
        return "sqlite:///:memory:"


ENV = os.getenv("FLASK_ENV")
DEBUG = ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "not-secret")


SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL")
#os.getenv("DATABASE_URI", default=get_db_url())
SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

APP_KEY = os.getenv("APP_KEY", default="admin")
APP_SECRET = os.getenv("APP_SECRET", default="admin")
