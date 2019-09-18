from flask import current_app as app
from flask import json, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate
from sqlalchemy import and_

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import LpoItem, LocalPurchaseOrder, Item
from autoshop.api.resources.local_purchase_order import LocalPurchaseOrderSchema
from autoshop.api.resources.item import ItemSchema

class LpoItemSchema(ma.ModelSchema):
    item = ma.Nested(ItemSchema, only=('name','uuid'))
    order = ma.Nested(LocalPurchaseOrderSchema, only=('id','uuid', 'vendor_id'))
    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")
    
    order_id = ma.String(required=True)
    item_id = ma.String(required=True, validate=[not_empty])
    quantity = ma.Integer(required=True)
    unit_price = ma.Integer(required=True)

    class Meta:
        model = LpoItem
        sqla_session = db.session

        additional = ("creator", "amount")


class LpoItemResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, lpo_item_id):
        schema = LpoItemSchema()
        lpo_item = LpoItem.query.get_or_404(lpo_item_id)
        return {"lpo_item": schema.dump(lpo_item).data}

    def put(self, lpo_item_id):
        identity = get_jwt_identity()

        schema = LpoItemSchema(partial=True)
        lpo_item = LpoItem.query.get_or_404(lpo_item_id)
        lpo_item, errors = schema.load(request.json, instance=lpo_item)
        if errors:
            return errors, 422

        lpo_item.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "lpo_item updated", "lpo_item": schema.dump(lpo_item).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, lpo_item_id):
        lpo_item = LpoItem.query.get_or_404(lpo_item_id)
        db.session.delete(lpo_item)
        db.session.commit()

        return {"msg": "lpo_item deleted"}


class LpoItemList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = LpoItemSchema(many=True)
        code = request.args.get("code")
        amount = request.args.get("amount")

        if code:
            query = LpoItem.query.filter_by(order_id=code)
        else:
            query = LpoItem.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = LpoItemSchema()
        lpo_item, errors = schema.load(request.json)
        if errors:
            return errors, 422

        lpo_item.created_by = identity

        try:
            if not LocalPurchaseOrder.get(uuid=lpo_item.order_id):
                return {"msg": "The supplied lpo code doesnt exist"}, 422
            if LpoItem.get(order_id=lpo_item.order_id, item_id=lpo_item.item_id):
                return {"msg": "The supplied lpo_item already exists"}, 409
            else:

                lpo = LocalPurchaseOrder.get(uuid=lpo_item.order_id)
                lpo_item.entity_id = lpo.entity_id

                db.session.add(lpo_item)
                db.session.commit()
                return (
                    {"msg": "lpo_item created", "lpo_item": schema.dump(lpo_item).data},
                    201,
                )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500

