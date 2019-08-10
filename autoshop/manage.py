#!/usr/bin/python
# -*- coding: utf-8 -*-
import click
import os
from flask.cli import FlaskGroup
from flask import current_app as app

from autoshop.app import create_app
from autoshop.extensions import db
from autoshop.commons.dbaccess import execute_sql
from autoshop.models import User, Role, PaymentType, TransactionType, \
    CustomerType, Entity, Account


def create_autoshop(info):
    return create_app(cli=True)


@click.group(cls=FlaskGroup, create_app=create_autoshop)
def cli():
    """Main entry point"""


@cli.command('reset')
def reset():
    """Drop db and remove migrations
    """

    click.echo('remove migrations and drop db')
    os.system('rm -rf migrations')
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/drop.sql')
    file = open(filename)
    execute_sql(file)
    db.drop_all()


@cli.command('seed')
def seed():
    import datetime

    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/makes.sql')
    file = open(filename)
    execute_sql(file)

    entity = Entity(
        name='Floben Autoshop',
        email='info@floben.ug',
        phone='256770443322',
        address='Ntinda',
        created_by=1,
        date_created=datetime.datetime.now(),
        )

    account = Account(owner_id=entity.uuid, acc_type='entity',
                      created_by=1, group=entity.uuid)

    db.session.add(entity)
    db.session.add(account)

    ctype = CustomerType(uuid='in_fleet', name='IN FLEET',
                         created_by=1, entity_id=entity.uuid)
    ctype1 = CustomerType(uuid='out_fleet', name='OUT FLEET',
                          created_by=1, entity_id=entity.uuid)

    db.session.add(ctype1)
    db.session.add(ctype)
    db.session.commit()


@cli.command('items')
def items():
    """item_views create
    """

    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/items.sql')
    file = open(filename)
    execute_sql(file)


@cli.command('recreate_views')
def recreate_views():
    """Drop views and recreate
    """

    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/views.sql')
    file = open(filename)
    execute_sql(file)


@cli.command('truncate')
def truncate():
    """truncate
    """

    click.echo('remove migrations and truncate')
    os.system('rm -rf migrations')
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/truncate.sql')
    file = open(filename)
    execute_sql(file)


@cli.command('strip')
def strip():
    paths = ['autoshop/api/resources', 'autoshop/models',
             'autoshop/manage.py']

    for path in paths:
        strip_in_path(path)


def strip_in_path(PATH):
    for (path, dirs, files) in os.walk(PATH):
        for f in files:
            (file_name, file_extension) = os.path.splitext(f)
            if file_extension == '.py':
                path_name = os.path.join(path, f)
                with open(path_name, 'r') as fh:
                    new = [line.rstrip() for line in fh]
                with open(path_name, 'w') as fh:
                    [fh.write('%s\n' % line) for line in new]


@cli.command('init')
def init():
    """Init application, create database tables
    and create a new user named admin with password admin
    """

    click.echo('create database')
    db.create_all()
    click.echo('done')

    click.echo('add account balances view')
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/accounting.sql')
    file = open(filename)
    execute_sql(file)
    click.echo('add other views')
    filename2 = os.path.join(fileDir, 'autoshop/sql/views.sql')
    file2 = open(filename2)
    execute_sql(file2)

    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, 'autoshop/sql/items.sql')
    file = open(filename)
    execute_sql(file)

    click.echo('create user')
    role = Role(uuid='system_admin', name='System Admin',
                category='system', active=True, created_by=1)
    role2 = Role(uuid='system_user', name='System User',
                 category='system', active=True, created_by=1)
    role3 = Role(uuid='entity_admin', name='Entity Admin',
                 category='entity', active=True, created_by=1)
    role4 = Role(uuid='vendor_user', name='Vendor User',
                 category='vendor', active=True, created_by=1)

    pay_type = PaymentType(uuid='momo', name='Mobile Money',
                           active=True, created_by=1)
    pay_type2 = PaymentType(uuid='cash', name='Cash', active=True,
                            created_by=1)

    tran_type = TransactionType(uuid='bill', name='Bill', active=True,
                                created_by=1)
    tran_type2 = TransactionType(uuid='payment', name='Payment',
                                 active=True, created_by=1)
    tran_type3 = TransactionType(uuid='reversal', name='Reversal',
                                 active=True, created_by=1)
    tran_type4 = TransactionType(uuid='adjustment', name='Adjustment',
                                 active=True, created_by=1)

    user = User(
        username=app.config['APP_KEY'],
        first_name='System',
        last_name='Administrator',
        email='admin@mail.com',
        password=app.config['APP_SECRET'],
        role_code='system_admin',
        active=True,
        company_id='system',
        )

    pay_type.save()
    pay_type2.save()
    db.session.add(tran_type)
    db.session.add(tran_type2)
    db.session.add(tran_type3)
    db.session.add(tran_type4)
    db.session.add(role)
    db.session.add(role2)
    db.session.add(role3)
    db.session.add(role4)
    db.session.add(user)
    db.session.commit()
    click.echo('created user admin')


if __name__ == '__main__':
    cli()
