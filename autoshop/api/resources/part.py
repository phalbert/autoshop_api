from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Part, Entity, VehicleModel, PartCategory
from autoshop.api.resources.part_category import PartCategorySchema
from autoshop.api.resources.vehicle_model import VehicleModelSchema
from autoshop.api.resources.entity import EntitySchema
from autoshop.api.resources.vendor import VendorSchema

class PartSchema(ma.ModelSchema):
    
    entity = ma.Nested(EntitySchema, only=('name','address','email', 'phone'))
    category = ma.Nested(PartCategorySchema)
    vendor = ma.Nested(VendorSchema)

    name = ma.String(required=True)
    code = ma.String(required=True)
    model_id = ma.String(required=True)
    category_id = ma.String(required=True)
    price = ma.Integer(required=True)
    vendor_price = ma.Integer(required=True)
    quantity = ma.Integer(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = Part
        sqla_session = db.session

        additional = ("creator",)


class PartResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, setting_id):
        schema = PartSchema()
        part = Part.query.get_or_404(setting_id)
        return {"part": schema.dump(part).data}

    def put(self, setting_id):
        schema = PartSchema(partial=True)
        part = Part.query.get_or_404(setting_id)
        part, errors = schema.load(request.json, instance=part)
        if errors:
            return errors, 422
        part.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "part updated", "part": schema.dump(part).data}

    def delete(self, setting_id):
        part = Part.query.get_or_404(setting_id)
        db.session.delete(part)
        db.session.commit()

        return {"msg": "part deleted"}


class PartList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = PartSchema(many=True)
        query = Part.query
        return paginate(query, schema)

    def post(self):
        schema = PartSchema()
        part, errors = schema.load(request.json)
        if errors:
            return errors, 422

        part.created_by = get_jwt_identity()
        
        if not Entity.get(uuid=part.entity_id):
            return {"msg": "The supplied entity id does not exist"}, 422        
        if Part.get(name=part.name):
            return {"msg": "The supplied name already exists"}, 409
        if not VehicleModel.get(uuid=part.model_id):
            return {"msg": "The supplied vehicle model doesnt exist"}, 422
        if not PartCategory.get(uuid=part.category_id):
            return {"msg": "The supplied part category doesnt exist"}, 422

        db.session.add(part)
        db.session.commit()

        return {"msg": "part created", "part": schema.dump(part).data}, 201
