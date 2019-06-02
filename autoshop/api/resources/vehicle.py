from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Vehicle


class VehicleSchema(ma.ModelSchema):
    registration_no = ma.String(required=True)
    chassis_no = ma.String(required=True)
    model = ma.String(required=True)
    model_no = ma.String(required=True)
    engine_no = ma.String(required=True)
    vehicle_type = ma.String(required=True)
    customer_id = ma.String(required=True)

    class Meta:
        model = Vehicle
        sqla_session = db.session

        additional = ("creator",)


class VehicleResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, vehicle_id):
        schema = VehicleSchema()
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        return {"vehicle": schema.dump(vehicle).data}

    def put(self, vehicle_id):
        schema = VehicleSchema(partial=True)
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        vehicle, errors = schema.load(request.json, instance=vehicle)
        if errors:
            return errors, 422
        vehicle.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "vehicle updated", "vehicle": schema.dump(vehicle).data}

    def delete(self, vehicle_id):
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        db.session.delete(vehicle)
        db.session.commit()

        return {"msg": "vehicle deleted"}


class VehicleList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = VehicleSchema(many=True)
        query = Vehicle.query
        return paginate(query, schema)

    def post(self):
        schema = VehicleSchema()
        vehicle, errors = schema.load(request.json)
        if errors:
            return errors, 422

        vehicle.created_by = get_jwt_identity()

        if Vehicle.get(registration_no=vehicle.registration_no, customer_id=vehicle.customer_id):
            return {"msg": "The supplied vehicle already exists"}, 409

        db.session.add(vehicle)
        db.session.commit()

        return {"msg": "vehicle created", "vehicle": schema.dump(vehicle).data}, 201
