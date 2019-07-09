from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.dbaccess import query
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Customer, Entity, Vendor


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        sqla_session = db.session

        additional = ("creator", "balance", "name", "wallets")


class AccountResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, user_id):
        schema = AccountSchema()
        account = Account.query.get_or_404(user_id)
        return {"account": schema.dump(account).data}

    def put(self, user_id):
        schema = AccountSchema(partial=True)
        account = Account.query.get_or_404(user_id)
        account, errors = schema.load(request.json, instance=account)
        if errors:
            return errors, 422

        return {"msg": "account updated", "account": schema.dump(account).data}

    def delete(self, user_id):
        account = Account.query.get_or_404(user_id)
        db.session.delete(account)
        db.session.commit()

        return {"msg": "account deleted"}


class AccountList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = AccountSchema(many=True)

        if request.args.get("owner") is not None:
            query = Account.query.filter_by(owner_id=request.args.get("owner"))
        elif request.args.get("type") is not None:
            query = Account.query.filter_by(acc_type=request.args.get("type"))
        elif request.args.get("uuid") is not None:
            query = Account.query.filter_by(uuid=request.args.get("uuid"))
        elif request.args.get("entity") is not None:
            query = Account.query.filter_by(group=request.args.get("entity"))
        else:
            query = Account.query
        return paginate(query, schema)

    def post(self):
        schema = AccountSchema()
        account, errors = schema.load(request.json)
        if errors:
            return errors, 422

        account.created_by = get_jwt_identity()

        if (
            not Customer.get(uuid=account.owner_id)
            and not Entity.get(uuid=account.owner_id)
            and not Vendor.get(uuid=account.owner_id)
        ):
            return {"msg": "The supplied owner id doesnt exist"}, 409

        try:
            db.session.add(account)
            db.session.commit()

            return {"msg": "account created", "account": schema.dump(account).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, 500


class AccountEntriesResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, account_id):
        sql = (
            """ 0 as entry_id,'' as tran_type,'credit' as tran_category,
                (select date_created from accounts where id="""
            + str(account_id)
            + """)
                as date_created,0 as amount,0 as balance
                union
                select entry_id,tran_type,tran_category,date_created,amount,
                (select sum(amount) from account_ledgers b where account_id="""
            + str(account_id)
            + """
                and b.entry_id<=a.entry_id ) as balance from account_ledgers a
                where account_id="""
            + str(account_id)
            + """
                order by entry_id desc"""
        )

        response = query(sql)
        return response, 200


class AccountEntriesList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        sql = """ V.entry_id,account_id,B.uuid,H.name, V.reference, V.tran_type,V.tran_category,
        V.date_created,amount, e.name as entity_id FROM account_ledgers AS V
        inner join accounts AS B on B.id=V.account_id inner join account_holders H on
        B.owner_id=H.uuid inner join entity e on e.uuid=V.entity_id """

        if request.args.get("company") is not None:
            where = " where entity_id='" + request.args.get("company") + "'"
            sql = sql + where

        order_by = " order by V.date_created desc,  V.entry_id desc, V.amount desc"
        sql = sql + order_by

        response = query(sql)
        return response, 200
