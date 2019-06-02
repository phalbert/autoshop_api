"""Default configuration

Use env var to override
"""
import os

ENV = os.getenv("FLASK_ENV")
DEBUG = ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "not-secret")

DATABASE_URL="postgresql://hpal:yujiku@localhost:5432/autoshop"

SQLALCHEMY_DATABASE_URI = DATABASE_URL #os.getenv("DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

APP_KEY = os.getenv("APP_KEY", default="admin")
APP_SECRET = os.getenv("APP_SECRET", default="admin")
