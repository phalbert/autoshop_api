from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Item, Entity, VehicleModel, ItemCategory
from autoshop.api.resources.item_category import ItemCategorySchema
from autoshop.api.resources.entity import EntitySchema
from autoshop.api.resources.vendor import VendorSchema


class ItemSchema(ma.ModelSchema):

    entity = ma.Nested(EntitySchema, only=('name', 'address', 'email', 'phone'))
    category = ma.Nested(ItemCategorySchema)
    vendor = ma.Nested(VendorSchema)

    name = ma.String(required=True)
    code = ma.String(required=True)
    model_id = ma.String(required=True)
    category_id = ma.String(required=True)
    price = ma.Integer(required=True)
    make_id = ma.Integer(required=True)
    item_type = ma.String(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = Item
        sqla_session = db.session

        additional = ("creator", "quantity")


class ItemResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, item_id):
        schema = ItemSchema()
        item = Item.query.get_or_404(item_id)
        return {"item": schema.dump(item).data}

    def put(self, item_id):
        schema = ItemSchema(partial=True)
        item = Item.query.get_or_404(item_id)
        item, errors = schema.load(request.json, instance=item)
        if errors:
            return errors, 422
        item.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "item updated", "item": schema.dump(item).data}

    def delete(self, item_id):
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()

        return {"msg": "item deleted"}


class ItemList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ItemSchema(many=True)

        if request.args.get("uuid") is not None:
            query = Item.query.filter_by(uuid=request.args.get("uuid"))
        else:
            query = Item.query
        return paginate(query, schema)

    def post(self):
        schema = ItemSchema()
        item, errors = schema.load(request.json)
        if errors:
            return errors, 422

        item.created_by = get_jwt_identity()

        if not Entity.get(uuid=item.entity_id):
            return {"msg": "The supplied entity id does not exist"}, 422
        if Item.get(name=item.name):
            return {"msg": "The supplied name already exists"}, 409
        if Item.get(code=item.code):
            return {"msg": "The supplied code already exists"}, 409
        if item.model_id != 'ALL' and not VehicleModel.get(uuid=item.model_id):
            return {"msg": "The supplied vehicle model doesnt exist"}, 422
        if not ItemCategory.get(uuid=item.category_id):
            return {"msg": "The supplied item category doesnt exist"}, 422

        db.session.add(item)
        db.session.commit()

        return {"msg": "item created", "item": schema.dump(item).data}, 201
