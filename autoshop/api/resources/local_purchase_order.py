from datetime import datetime

from flask import request, current_app as app
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.entity import EntitySchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, LocalPurchaseOrder, Vendor
from autoshop.api.resources.vendor import VendorSchema
class LocalPurchaseOrderSchema(ma.ModelSchema):
    entity = ma.Nested(EntitySchema, only=('name','address','email', 'phone'))
    vendor = ma.Nested(VendorSchema, only=('name','address','email', 'phone'))
    
    vendor_id = ma.String(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = LocalPurchaseOrder
        sqla_session = db.session

        additional = ("creator", "items", "credit")


class LocalPurchaseOrderResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, lpo_id):
        schema = LocalPurchaseOrderSchema()
        lpo = LocalPurchaseOrder.query.get_or_404(lpo_id)
        return {"lpo": schema.dump(lpo).data}

    def put(self, lpo_id):
        schema = LocalPurchaseOrderSchema(partial=True)
        lpo = LocalPurchaseOrder.query.get_or_404(lpo_id)
        lpo, errors = schema.load(request.json, instance=lpo)
        if errors:
            return errors, 422
        try:
            if request.json.get('status') == 'COMPLETED':
                lpo.log_items()
            else:
                amount_to_pay = request.json.get('amount_to_pay')
                lpo.clear_credit(amount_to_pay)
            return {"msg": "lpo updated", "lpo": schema.dump(lpo).data}
        except Exception as e:
            lpo.credit_status = 'PARTIAL'
            if request.json.get('status') == 'COMPLETED':
                lpo.status = 'PENDING'
            lpo.update()
            return {"msg": e.args[0]}, e.args[1] if len(e.args) > 1 else 500

    def delete(self, lpo_id):
        lpo = LocalPurchaseOrder.query.get_or_404(lpo_id)
        db.session.delete(lpo)
        db.session.commit()

        return {"msg": "lpo deleted"}


class LocalPurchaseOrderList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = LocalPurchaseOrderSchema(many=True)

        if request.args.get("uuid") and request.args.get("tran_type"):
            query = LocalPurchaseOrder.query.filter_by(
                entity_id=request.args.get("uuid"),
                tran_type=request.args.get("tran_type"),
            )
        elif request.args.get("uuid"):
            vendor = Vendor.get(uuid=request.args.get("uuid"))
            if vendor:
                query = LocalPurchaseOrder.query.filter_by(credit=vendor.account.id)
            else:
                query = LocalPurchaseOrder.query.filter_by(entity_id=request.args.get("uuid"))
        elif request.args.get("reference"):
            query = LocalPurchaseOrder.query.filter_by(reference=request.args.get("reference"))
        elif request.args.get("code"):
            query = LocalPurchaseOrder.query.filter_by(uuid=request.args.get("code"))
        else:
            query = LocalPurchaseOrder.query
        query = query.order_by(LocalPurchaseOrder.date_created.desc())
        return paginate(query, schema)

    def post(self):
        schema = LocalPurchaseOrderSchema()
        lpo, errors = schema.load(request.json)
        if errors:
            return errors, 422

        try:
            lpo.save()
            return {"msg": "lpo created", "lpo": schema.dump(lpo).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500
