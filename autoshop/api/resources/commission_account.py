from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from autoshop.models import Account, CommissionAccount, Customer, Entity, Vendor
from autoshop.extensions import ma, db
from autoshop.commons.pagination import paginate
from autoshop.commons.dbaccess import query
from autoshop.api.resources.account import AccountSchema

class CommissionAccountSchema(ma.ModelSchema):

    account = ma.Nested(AccountSchema)

    entity_id = ma.String(required=True)
    code = ma.String(required=True)
    name = ma.String(required=True)

    class Meta:
        model = CommissionAccount
        sqla_session = db.session

        additional = ('creator',)


class CommissionAccountResource(Resource):
    """Single object resource
    """
    method_decorators = [jwt_required]

    def get(self, comm_account_id):
        schema = CommissionAccountSchema()
        comm_account = CommissionAccount.query.get_or_404(comm_account_id)
        return {"comm_account": schema.dump(comm_account).data}

    def put(self, comm_account_id):
        schema = CommissionAccountSchema(partial=True)
        comm_account = CommissionAccount.query.get_or_404(comm_account_id)
        comm_account, errors = schema.load(request.json, instance=comm_account)
        if errors:
            return errors, 422
        db.session.commit()
        return {"msg": "comm_account updated", "comm_account": schema.dump(comm_account).data}

    def delete(self, user_id):
        comm_account = CommissionAccount.query.get_or_404(user_id)
        db.session.delete(comm_account)
        db.session.commit()

        return {"msg": "comm_account deleted"}


class CommissionAccountList(Resource):
    """Creation and get_all
    """
    method_decorators = [jwt_required]

    def get(self):
        schema = CommissionAccountSchema(many=True)

        if request.args.get('code') is not None and request.args.get('entity'):
            code = request.args.get('code')
            entity = request.args.get('entity')
            query = CommissionAccount.query.filter_by(code=code, entity_id=entity)
        elif request.args.get('entity') is not None:
            query = CommissionAccount.query.filter_by(entity_id=request.args.get('entity'))
        elif request.args.get('code') is not None:
            query = CommissionAccount.query.filter_by(code=request.args.get('code'))
        elif request.args.get('uuid') is not None:
            query = CommissionAccount.query.filter_by(uuid=request.args.get('uuid'))
        else:
            query = CommissionAccount.query
        return paginate(query, schema)

    def post(self):
        schema = CommissionAccountSchema()
        comm_account, errors = schema.load(request.json)
        if errors:
            return errors, 422

        comm_account.created_by = get_jwt_identity()


        if not Entity.get(uuid=comm_account.entity_id) and not Vendor.get(uuid=comm_account.entity_id):
            return {"msg": "The supplied entity id doesnt exist"}, 422

        try:
            comm_account.save()

            return {"msg": "comm_account created", "comm_account": schema.dump(comm_account).data}, 201
        except Exception as e:
            db.session.rollback()

            return {"msg": e.args[0]}, 500

