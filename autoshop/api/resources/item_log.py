from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.entity import EntitySchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import ItemLog, Vendor
from autoshop.api.resources.item import ItemSchema


class ItemLogSchema(ma.ModelSchema):
    item = ma.Nested(ItemSchema, only=('name', 'uuid'))

    entity = ma.Nested(EntitySchema, only=('name', 'address', 'email', 'phone'))

    item_id = ma.String(required=True)
    debit = ma.String(required=True)
    credit = ma.String(required=True)
    reference = ma.String(required=True)
    category = ma.String(required=True)
    quantity = ma.Integer(required=True)
    amount = ma.Integer(required=True)
    unit_cost = ma.Integer(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = ItemLog
        sqla_session = db.session

        additional = ("debit_account", "credit_account", "creator")


class ItemLogResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, item_log_id):
        schema = ItemLogSchema()
        item_log = ItemLog.query.get_or_404(item_log_id)
        return {"item_log": schema.dump(item_log).data}

    def put(self, item_log_id):
        schema = ItemLogSchema(partial=True)
        item_log = ItemLog.query.get_or_404(item_log_id)
        item_log, errors = schema.load(request.json, instance=item_log)
        if errors:
            return errors, 422

        return {"msg": "item_log updated", "item_log": schema.dump(item_log).data}

    def delete(self, item_log_id):
        item_log = ItemLog.query.get_or_404(item_log_id)
        db.session.delete(item_log)
        db.session.commit()

        return {"msg": "item_log deleted"}


class ItemLogList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ItemLogSchema(many=True)
        
        if request.args.get("type"):
            from_date = request.args.get('from')
            to_date = request.args.get('to')
            tran_type = request.args.get('type')
            item = request.args.get('item_id')
            query = ItemLog.query.filter_by(category=tran_type)
            if item:
                query = ItemLog.query.filter_by(category=tran_type, item_id=item)
            if from_date and to_date:
                query = query.filter(ItemLog.date_created.between(from_date,to_date))


        elif request.args.get("uuid") and request.args.get("tran_type"):
            query = ItemLog.query.filter_by(
                entity_id=request.args.get("uuid"),
                category=request.args.get("tran_type"),
            )
        elif request.args.get("uuid"):
            vendor = Vendor.get(uuid=request.args.get("uuid"))
            if vendor:
                query = ItemLog.query.filter_by(credit=vendor.account.id)
            else:
                query = ItemLog.query.filter_by(entity_id=request.args.get("uuid"))
        elif request.args.get("reference"):
            query = ItemLog.query.filter_by(reference=request.args.get("reference"))
        elif request.args.get("entity") is not None:
            query = ItemLog.query.filter_by(entity_id=request.args.get("entity"))
        else:
            query = ItemLog.query
        query = query.order_by(ItemLog.date_created.desc())
        return paginate(query, schema)

    def post(self):
        schema = ItemLogSchema()
        item_log, errors = schema.load(request.json)
        if errors:
            return errors, 422

        item_log.created_by = get_jwt_identity()
        item_log.accounting_period = datetime.now().strftime("%Y-%m")

        try:
            item_log.transact()
            return {"msg": "item_log created", "item_log": schema.dump(item_log).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, e.args[1] if len(e.args) > 1 else 500
