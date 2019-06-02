from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import TransactionType


class TransactionTypeSchema(ma.ModelSchema):
    class Meta:
        model = TransactionType
        sqla_session = db.session

        additional = ("creator",)


class TransactionTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, transaction_type_id):
        schema = TransactionTypeSchema()
        transaction_type = TransactionType.query.get_or_404(transaction_type_id)
        return {"transaction_type": schema.dump(transaction_type).data}

    def put(self, transaction_type_id):
        schema = TransactionTypeSchema(partial=True)
        transaction_type = TransactionType.query.get_or_404(transaction_type_id)
        transaction_type, errors = schema.load(request.json, instance=transaction_type)
        if errors:
            return errors, 422
        transaction_type.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "transaction_type updated",
            "transaction_type": schema.dump(transaction_type).data,
        }

    def delete(self, transaction_type_id):
        transaction_type = TransactionType.query.get_or_404(transaction_type_id)
        db.session.delete(transaction_type)
        db.session.commit()

        return {"msg": "transaction_type deleted"}


class TransactionTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = TransactionTypeSchema(many=True)
        if request.args.get("uuid") is not None:
            uuid = request.args.get("uuid")
            query = TransactionType.query.filter_by(uuid=uuid)
        else:
            query = TransactionType.query
        return paginate(query, schema)

    def post(self):
        schema = TransactionTypeSchema()
        transaction_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        transaction_type.created_by = get_jwt_identity()

        if TransactionType.get(name=transaction_type.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(transaction_type)
        db.session.commit()

        return (
            {
                "msg": "transaction_type created",
                "transaction_type": schema.dump(transaction_type).data,
            },
            201,
        )
