from flask import current_app as app
from flask import json, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate
from sqlalchemy import and_

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Charge, Tarriff


class ChargeSchema(ma.ModelSchema):
    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")
    types = validate.OneOf(["flat", "percentage"])

    code = ma.String(required=True, validate=[not_empty])
    min_value = ma.Integer(required=True)
    max_value = ma.Integer(required=True)
    amount = ma.Integer(required=True)
    charge_type = ma.String(required=True, validate=[types])

    class Meta:
        model = Charge
        sqla_session = db.session

        additional = ("tarriff",)


class ChargeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, charge_id):
        schema = ChargeSchema()
        charge = Charge.query.get_or_404(charge_id)
        return {"charge": schema.dump(charge).data}

    def put(self, charge_id):
        identity = get_jwt_identity()

        schema = ChargeSchema(partial=True)
        charge = Charge.query.get_or_404(charge_id)
        charge, errors = schema.load(request.json, instance=charge)
        if errors:
            return errors, 422

        charge.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "charge updated", "charge": schema.dump(charge).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, charge_id):
        charge = Charge.query.get_or_404(charge_id)
        db.session.delete(charge)
        db.session.commit()

        return {"msg": "charge deleted"}


class ChargeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ChargeSchema(many=True)
        chargecode = request.args.get("code")
        amount = request.args.get("amount")

        if chargecode and amount:
            # query = get_charge(chargecode, amount)
            query = Charge.query.filter(
                and_(
                    Charge.code == chargecode,
                    Charge.min_value <= amount,
                    Charge.max_value >= amount,
                )
            ).first()
            app.logger.info(query.amount)
            if query.charge_type == "percentage":
                charge_fee = (int(query.amount) / 100) * int(amount)
                response = {"charge": charge_fee}
            else:
                response = {"charge": query.amount}
            return json.dumps(response), 207

        elif chargecode:
            query = Charge.query.filter_by(code=chargecode)
        else:
            query = Charge.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = ChargeSchema()
        charge, errors = schema.load(request.json)
        if errors:
            return errors, 422

        charge.created_by = identity

        try:
            if not Tarriff.get(uuid=charge.code):
                return {"msg": "The supplied charge code doesnt exist"}, 422
            if Charge.get(
                uuid=charge.code, min_value=charge.min_value, max_value=charge.max_value
            ):
                return {"msg": "The supplied charge range already exists"}, 409
            if (
                charge.min_value > charge.max_value
                or charge.min_value == charge.max_value
            ):
                return (
                    {
                        "msg": "The minimum value cannot be greater than or equal to the maximum value"
                    },
                    422,
                )
            # check if a range exists where the min value falls
            if get_charge(charge.code, charge.min_value):
                return (
                    {"msg": "The supplied minimum value falls in an existing range"},
                    422,
                )
            # check if a range exists where the max value falls
            if get_charge(charge.code, charge.max_value):
                return (
                    {"msg": "The supplied maximum value falls in an existing range"},
                    422,
                )
            else:
                db.session.add(charge)
                db.session.commit()
                return (
                    {"msg": "charge created", "charge": schema.dump(charge).data},
                    201,
                )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500


def get_charge(charge_code, charge_value):
    result = Charge.query.filter(
        and_(
            Charge.code == charge_code,
            Charge.min_value <= charge_value,
            Charge.max_value >= charge_value,
        )
    ).all()
    return result
