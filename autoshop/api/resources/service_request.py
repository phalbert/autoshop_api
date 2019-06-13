from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import (
    Entity, ServiceRequest, TransactionType
)
from autoshop.api.resources.vehicle import VehicleSchema
from autoshop.api.resources.service import ServiceSchema
from autoshop.api.resources.customer import CustomerSchema
from autoshop.api.resources.entity import EntitySchema

class ServiceRequestSchema(ma.ModelSchema):
    vehicle = ma.Nested(VehicleSchema)
    service = ma.Nested(ServiceSchema)
    customer = ma.Nested(CustomerSchema, only=('name','address','email', 'phone'))
    entity = ma.Nested(EntitySchema, only=('name','address','email', 'phone'))

    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")
    pay_types = validate.OneOf(["cash", "momo"])

    customer_id = ma.String(required=True, validate=[not_empty])
    service_id = ma.String(required=True, validate=[not_empty])
    vehicle_id = ma.String(required=True, validate=[not_empty])
    entity_id = ma.String(required=True, validate=[not_empty])

    class Meta:
        model = ServiceRequest
        sqla_session = db.session


class ServiceRequestResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, service_request_id):
        schema = ServiceRequestSchema()
        service_request = ServiceRequest.query.get_or_404(service_request_id)
        return {"service_request": schema.dump(service_request).data}

    def put(self, service_request_id):
        identity = get_jwt_identity()

        schema = ServiceRequestSchema(partial=True)
        service_request = ServiceRequest.query.get_or_404(service_request_id)
        service_request, errors = schema.load(request.json, instance=service_request)
        if errors:
            return errors, 422

        service_request.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "service_request updated", "service_request": schema.dump(service_request).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, service_request_id):
        service_request = ServiceRequest.query.get_or_404(service_request_id)
        db.session.delete(service_request)
        db.session.commit()

        return {"msg": "service_request deleted"}


class ServiceRequestList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ServiceRequestSchema(many=True)
        service_requestcode = request.args.get("code")
        if service_requestcode is not None:
            query = ServiceRequest.query.filter_by(uuid=service_requestcode)
        else:
            query = ServiceRequest.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = ServiceRequestSchema()
        service_request, errors = schema.load(request.json)
        if errors:
            return errors, 422

        service_request.created_by = identity


        try:
            db.session.add(service_request)
            db.session.commit()
            return (
                {"msg": "service_request created", "service_request": schema.dump(service_request).data},
                201,
            )
                
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0], "exception": e.args}, 500
