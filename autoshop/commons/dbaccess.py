import psycopg2
import sqlalchemy
from flask import current_app


def query(sql):
    current_app.logger.info(sql)
    conn = psycopg2.connect(current_app.config["SQLALCHEMY_DATABASE_URI"])
    cursor = conn.cursor()
    cursor.execute("select json_agg(t) from (SELECT " + sql + ")  t")
    rows = cursor.fetchall()
    conn.close()
    return rows[0][0]


def execute_sql(file):
    # file = open(file_path)
    engine = sqlalchemy.create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])
    escaped_sql = sqlalchemy.text(file.read())
    engine.execute(escaped_sql)


def search(query):
    conn = psycopg2.connect(current_app.config["SQLALCHEMY_DATABASE_URI"])
    cursor = conn.cursor()
    cursor.execute("select json_agg(t) from (SELECT * FROM " + query + ")  t")
    rows = cursor.fetchall()
    conn.close()
    return rows[0][0]
