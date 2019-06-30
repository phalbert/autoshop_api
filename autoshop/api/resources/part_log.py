from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.entity import EntitySchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, PartLog, Vendor
from autoshop.api.resources.part import PartSchema

class PartLogSchema(ma.ModelSchema):
    part = ma.Nested(PartSchema, only=('name','vendor_price'))

    entity = ma.Nested(EntitySchema, only=('name','address','email', 'phone'))
    
    part_id = ma.String(required=True)
    debit = ma.String(required=True)
    credit = ma.String(required=True)
    reference = ma.String(required=True)
    category = ma.String(required=True)
    quantity = ma.Integer(required=True)
    amount = ma.Integer(required=True)
    unit_cost = ma.Integer(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = PartLog
        sqla_session = db.session

        additional = ("debit_account", "credit_account", "creator")


class PartLogResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, part_log_id):
        schema = PartLogSchema()
        part_log = PartLog.query.get_or_404(part_log_id)
        return {"part_log": schema.dump(part_log).data}

    def put(self, part_log_id):
        schema = PartLogSchema(partial=True)
        part_log = PartLog.query.get_or_404(part_log_id)
        part_log, errors = schema.load(request.json, instance=part_log)
        if errors:
            return errors, 422

        return {"msg": "part_log updated", "part_log": schema.dump(part_log).data}

    def delete(self, part_log_id):
        part_log = PartLog.query.get_or_404(part_log_id)
        db.session.delete(part_log)
        db.session.commit()

        return {"msg": "part_log deleted"}


class PartLogList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = PartLogSchema(many=True)

        if request.args.get("uuid") and request.args.get("tran_type"):
            query = PartLog.query.filter_by(
                entity_id=request.args.get("uuid"),
                tran_type=request.args.get("tran_type"),
            )
        elif request.args.get("uuid"):
            vendor = Vendor.get(uuid=request.args.get("uuid"))
            if vendor:
                query = PartLog.query.filter_by(credit=vendor.account.id)
            else:
                query = PartLog.query.filter_by(entity_id=request.args.get("uuid"))
        elif request.args.get("reference"):
            query = PartLog.query.filter_by(reference=request.args.get("reference"))
        else:
            query = PartLog.query
        query = query.order_by(PartLog.date_created.desc(), PartLog.amount.desc())
        return paginate(query, schema)

    def post(self):
        schema = PartLogSchema()
        part_log, errors = schema.load(request.json)
        if errors:
            return errors, 422

        part_log.created_by = get_jwt_identity()
        part_log.accounting_period = datetime.now().strftime("%Y-%m")

        try:
            if PartLog.get(reference=part_log.reference):
                return {"msg": "The supplied reference already exists"}, 409

            db.session.add(part_log)
            db.session.commit()
            return {"msg": "part_log created", "part_log": schema.dump(part_log).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500
