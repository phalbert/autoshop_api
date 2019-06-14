from flask import current_app as app
from flask import json, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate
from sqlalchemy import and_

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import WorkItem, ServiceRequest
from autoshop.api.resources.service_request import ServiceRequestSchema

class WorkItemSchema(ma.ModelSchema):
    request = ma.Nested(ServiceRequestSchema)
    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")
    
    request_id = ma.String(required=True)
    item = ma.String(required=True, validate=[not_empty])
    quantity = ma.Integer(required=True)
    unit_cost = ma.Integer(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = WorkItem
        sqla_session = db.session

        additional = ("creator", "cost")


class WorkItemResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, work_item_id):
        schema = WorkItemSchema()
        work_item = WorkItem.query.get_or_404(work_item_id)
        return {"work_item": schema.dump(work_item).data}

    def put(self, work_item_id):
        identity = get_jwt_identity()

        schema = WorkItemSchema(partial=True)
        work_item = WorkItem.query.get_or_404(work_item_id)
        work_item, errors = schema.load(request.json, instance=work_item)
        if errors:
            return errors, 422

        work_item.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "work_item updated", "work_item": schema.dump(work_item).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, work_item_id):
        work_item = WorkItem.query.get_or_404(work_item_id)
        db.session.delete(work_item)
        db.session.commit()

        return {"msg": "work_item deleted"}


class WorkItemList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = WorkItemSchema(many=True)
        code = request.args.get("code")
        amount = request.args.get("amount")

        if code:
            query = WorkItem.query.filter_by(request_id=code)
        else:
            query = WorkItem.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = WorkItemSchema()
        work_item, errors = schema.load(request.json)
        if errors:
            return errors, 422

        work_item.created_by = identity

        try:
            if not ServiceRequest.get(uuid=work_item.request_id):
                return {"msg": "The supplied service request code doesnt exist"}, 422
            if WorkItem.get(request_id=work_item.request_id, item=work_item.item):
                return {"msg": "The supplied work_item already exists"}, 409
            else:
                db.session.add(work_item)
                db.session.commit()
                return (
                    {"msg": "work_item created", "work_item": schema.dump(work_item).data},
                    201,
                )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500

