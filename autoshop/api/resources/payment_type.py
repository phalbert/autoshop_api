from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import PaymentType


class PaymentTypeSchema(ma.ModelSchema):
    class Meta:
        model = PaymentType
        sqla_session = db.session

        additional = ("creator",)


class PaymentTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, payment_type_id):
        schema = PaymentTypeSchema()
        payment_type = PaymentType.query.get_or_404(payment_type_id)
        return {"payment_type": schema.dump(payment_type).data}

    def put(self, payment_type_id):
        schema = PaymentTypeSchema(partial=True)
        payment_type = PaymentType.query.get_or_404(payment_type_id)
        payment_type, errors = schema.load(request.json, instance=payment_type)
        if errors:
            return errors, 422
        payment_type.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "payment_type updated",
            "payment_type": schema.dump(payment_type).data,
        }

    def delete(self, payment_type_id):
        payment_type = PaymentType.query.get_or_404(payment_type_id)
        db.session.delete(payment_type)
        db.session.commit()

        return {"msg": "payment_type deleted"}


class PaymentTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = PaymentTypeSchema(many=True)
        if request.args.get("uuid"):
            query = PaymentType.query.filter_by(uuid=request.args.get("uuid"))
        else:
            query = PaymentType.query
        return paginate(query.order_by(PaymentType.uuid.asc()), schema)

    def post(self):
        schema = PaymentTypeSchema()
        payment_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        payment_type.created_by = get_jwt_identity()

        if PaymentType.get(name=payment_type.name):
            return {"msg": "The supplied name already exists"}, 409

        payment_type.save()

        return (
            {
                "msg": "payment_type created",
                "payment_type": schema.dump(payment_type).data,
            },
            201,
        )
