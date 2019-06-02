from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import VehicleType


class VehicleTypeSchema(ma.ModelSchema):
    class Meta:
        model = VehicleType
        sqla_session = db.session

        additional = ("creator",)


class VehicleTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, vehicle_type_id):
        schema = VehicleTypeSchema()
        vehicle_type = VehicleType.query.get_or_404(vehicle_type_id)
        return {"vehicle_type": schema.dump(vehicle_type).data}

    def put(self, vehicle_type_id):
        schema = VehicleTypeSchema(partial=True)
        vehicle_type = VehicleType.query.get_or_404(vehicle_type_id)
        vehicle_type, errors = schema.load(request.json, instance=vehicle_type)
        if errors:
            return errors, 422
        vehicle_type.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "vehicle_type updated", "vehicle_type": schema.dump(vehicle_type).data}

    def delete(self, vehicle_type_id):
        vehicle_type = VehicleType.query.get_or_404(vehicle_type_id)
        db.session.delete(vehicle_type)
        db.session.commit()

        return {"msg": "vehicle_type deleted"}


class VehicleTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = VehicleTypeSchema(many=True)
        query = VehicleType.query
        return paginate(query, schema)

    def post(self):
        schema = VehicleTypeSchema()
        vehicle_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        vehicle_type.created_by = get_jwt_identity()

        if VehicleType.get(name=vehicle_type.name):
            return {"msg": "The supplied vehicle type already exists"}, 409

        db.session.add(vehicle_type)
        db.session.commit()

        return (
            {"msg": "vehicle_type created", "vehicle_type": schema.dump(vehicle_type).data},
            201,
        )
