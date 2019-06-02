from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import AccountType


class AccountTypeSchema(ma.ModelSchema):
    class Meta:
        model = AccountType
        sqla_session = db.session

        additional = ("creator",)


class AccountTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, user_id):
        schema = AccountTypeSchema()
        account_type = AccountType.query.get_or_404(user_id)
        return {"account_type": schema.dump(account_type).data}

    def put(self, user_id):
        schema = AccountTypeSchema(partial=True)
        account_type = AccountType.query.get_or_404(user_id)
        account_type, errors = schema.load(request.json, instance=account_type)
        if errors:
            return errors, 422

        return {
            "msg": "account_type updated",
            "account_type": schema.dump(account_type).data,
        }

    def delete(self, user_id):
        account_type = AccountType.query.get_or_404(user_id)
        db.session.delete(account_type)
        db.session.commit()

        return {"msg": "account_type deleted"}


class AccountTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = AccountTypeSchema(many=True)
        query = AccountType.query
        return paginate(query, schema)

    def post(self):
        schema = AccountTypeSchema()
        account_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        account_type.created_by = get_jwt_identity()

        if AccountType.get(name=account_type.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(account_type)
        db.session.commit()

        return (
            {
                "msg": "account_type created",
                "account_type": schema.dump(account_type).data,
            },
            201,
        )
