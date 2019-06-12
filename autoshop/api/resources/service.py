from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Entity, Service, TransactionType


class ServiceSchema(ma.ModelSchema):
    not_empty = validate.Length(min=1, max=50, error="Field cant be empty.")

    name = ma.String(required=True, validate=[not_empty])
    description = ma.String(required=True)
    entity_id = ma.String(required=True, validate=[not_empty])

    class Meta:
        model = Service
        sqla_session = db.session

class ServiceResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, service_id):
        schema = ServiceSchema()
        service = Service.query.get_or_404(service_id)
        return {"service": schema.dump(service).data}

    def put(self, service_id):
        identity = get_jwt_identity()

        schema = ServiceSchema(partial=True)
        service = Service.query.get_or_404(service_id)
        service, errors = schema.load(request.json, instance=service)
        if errors:
            return errors, 422

        service.modified_by = identity

        try:
            db.session.commit()
            return {"msg": "service updated", "service": schema.dump(service).data}
        except Exception as e:
            db.session.rollback()
            return {"msg": "post error", "exception": e.args}, 500

    def delete(self, service_id):
        service = Service.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()

        return {"msg": "service deleted"}


class ServiceList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ServiceSchema(many=True)
        servicecode = request.args.get("code")
        if servicecode is not None:
            query = Service.query.filter_by(uuid=servicecode)
        else:
            query = Service.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = ServiceSchema()
        service, errors = schema.load(request.json)
        if errors:
            return errors, 422

        service.created_by = identity

        try:
            if Service.get(name=service.name):
                return {"msg": "The supplied service name already exists"}, 409
            else:
                db.session.add(service)
                db.session.commit()
                return (
                    {"msg": "service created", "service": schema.dump(service).data},
                    201,
                )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0], "exception": e.args}, 500
