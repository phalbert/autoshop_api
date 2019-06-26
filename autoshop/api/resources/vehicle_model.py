from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import VehicleModel, VehicleType
from autoshop.api.resources.vehicle_type import VehicleTypeSchema

class VehicleModelSchema(ma.ModelSchema):
    type = ma.Nested(VehicleTypeSchema)

    type_id = ma.String(required=True)
    description = ma.String(required=True)
    name = ma.String(required=True)

    class Meta:
        model = VehicleModel
        sqla_session = db.session

        additional = ("creator",)


class VehicleModelResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, vehicle_model_id):
        schema = VehicleModelSchema()
        vehicle_model = VehicleModel.query.get_or_404(vehicle_model_id)
        return {"vehicle_model": schema.dump(vehicle_model).data}

    def put(self, vehicle_model_id):
        schema = VehicleModelSchema(partial=True)
        vehicle_model = VehicleModel.query.get_or_404(vehicle_model_id)
        vehicle_model, errors = schema.load(request.json, instance=vehicle_model)
        if errors:
            return errors, 422
        vehicle_model.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "vehicle_model updated",
            "vehicle_model": schema.dump(vehicle_model).data,
        }

    def delete(self, vehicle_model_id):
        vehicle_model = VehicleModel.query.get_or_404(vehicle_model_id)
        db.session.delete(vehicle_model)
        db.session.commit()

        return {"msg": "vehicle_model deleted"}


class VehicleModelList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = VehicleModelSchema(many=True)
        query = VehicleModel.query
        return paginate(query, schema)

    def post(self):
        schema = VehicleModelSchema()
        vehicle_model, errors = schema.load(request.json)
        if errors:
            return errors, 422

        vehicle_model.created_by = get_jwt_identity()
        
        if not VehicleType.get(uuid=vehicle_model.type_id):
            return {"msg": "The supplied vehicle type doesnt exist"}, 409
        if VehicleModel.get(name=vehicle_model.name):
            return {"msg": "The supplied vehicle_model already exists"}, 409

        db.session.add(vehicle_model)
        db.session.commit()

        return (
            {
                "msg": "vehicle_model created",
                "vehicle_model": schema.dump(vehicle_model).data,
            },
            201,
        )
