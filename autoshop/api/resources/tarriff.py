from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Entity, Tarriff, TransactionType


class TarriffSchema(ma.ModelSchema):
    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")
    pay_types = validate.OneOf(["cash", "momo"])

    name = ma.String(required=True, validate=[not_empty])
    tran_type = ma.String(required=True, validate=[not_empty])
    payment_type = ma.String(required=True, validate=[pay_types])
    entity_id = ma.String(required=True, validate=[not_empty])

    class Meta:
        model = Tarriff
        sqla_session = db.session


class TarriffResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, tarriff_id):
        schema = TarriffSchema()
        tarriff = Tarriff.query.get_or_404(tarriff_id)
        return {"tarriff": schema.dump(tarriff).data}

    def put(self, tarriff_id):
        identity = get_jwt_identity()

        schema = TarriffSchema(partial=True)
        tarriff = Tarriff.query.get_or_404(tarriff_id)
        tarriff, errors = schema.load(request.json, instance=tarriff)
        if errors:
            return errors, 422

        tarriff.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "tarriff updated", "tarriff": schema.dump(tarriff).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, tarriff_id):
        tarriff = Tarriff.query.get_or_404(tarriff_id)
        db.session.delete(tarriff)
        db.session.commit()

        return {"msg": "tarriff deleted"}


class TarriffList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = TarriffSchema(many=True)
        tarriffcode = request.args.get("code")
        if tarriffcode is not None:
            query = Tarriff.query.filter_by(uuid=tarriffcode)
        else:
            query = Tarriff.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = TarriffSchema()
        tarriff, errors = schema.load(request.json)
        if errors:
            return errors, 422

        tarriff.created_by = identity

        try:
            if not TransactionType.get(uuid=tarriff.tran_type):
                return {"msg": "The supplied transaction type doesn't exist"}, 422
            if Tarriff.get(name=tarriff.name):
                return {"msg": "The supplied tarriff name already exists"}, 409
            if tarriff.entity_id != "ALL" and not Entity.get(uuid=tarriff.entity_id):
                return {"msg": "The entity code supplied doesn't exist"}, 422
            if Tarriff.get(
                payment_type=tarriff.payment_type,
                tran_type=tarriff.tran_type,
                entity_id=tarriff.entity_id,
            ):
                return (
                    {"msg": "A tarriff with the specified criteria already exists"},
                    409,
                )
            else:
                db.session.add(tarriff)
                db.session.commit()
                return (
                    {"msg": "tarriff created", "tarriff": schema.dump(tarriff).data},
                    201,
                )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0], "exception": e.args}, 500
