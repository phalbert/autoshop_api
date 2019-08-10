from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import ItemCategory


class ItemCategorySchema(ma.ModelSchema):
    class Meta:
        model = ItemCategory
        sqla_session = db.session

        additional = ("creator", "parent")


class ItemCategoryResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, item_category_id):
        schema = ItemCategorySchema()
        item_category = ItemCategory.query.get_or_404(item_category_id)
        return {"item_category": schema.dump(item_category).data}

    def put(self, item_category_id):
        schema = ItemCategorySchema(partial=True)
        item_category = ItemCategory.query.get_or_404(item_category_id)
        item_category, errors = schema.load(request.json, instance=item_category)
        if errors:
            return errors, 422
        item_category.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "item_category updated", "item_category": schema.dump(item_category).data}

    def delete(self, item_category_id):
        item_category = ItemCategory.query.get_or_404(item_category_id)
        db.session.delete(item_category)
        db.session.commit()

        return {"msg": "item_category deleted"}


class ItemCategoryList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ItemCategorySchema(many=True)
        query = ItemCategory.query
        return paginate(query, schema)

    def post(self):
        schema = ItemCategorySchema()
        item_category, errors = schema.load(request.json)
        if errors:
            return errors, 422

        item_category.created_by = get_jwt_identity()

        if ItemCategory.get(name=item_category.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(item_category)
        db.session.commit()

        return {"msg": "item_category created", "item_category": schema.dump(item_category).data}, 201
