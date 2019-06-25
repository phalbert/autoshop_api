from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import PartCategory


class PartCategorySchema(ma.ModelSchema):
    class Meta:
        model = PartCategory
        sqla_session = db.session

        additional = ("creator",)


class PartCategoryResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, part_category_id):
        schema = PartCategorySchema()
        part_category = PartCategory.query.get_or_404(part_category_id)
        return {"part_category": schema.dump(part_category).data}

    def put(self, part_category_id):
        schema = PartCategorySchema(partial=True)
        part_category = PartCategory.query.get_or_404(part_category_id)
        part_category, errors = schema.load(request.json, instance=part_category)
        if errors:
            return errors, 422
        part_category.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "part_category updated", "part_category": schema.dump(part_category).data}

    def delete(self, part_category_id):
        part_category = PartCategory.query.get_or_404(part_category_id)
        db.session.delete(part_category)
        db.session.commit()

        return {"msg": "part_category deleted"}


class PartCategoryList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = PartCategorySchema(many=True)
        query = PartCategory.query
        return paginate(query, schema)

    def post(self):
        schema = PartCategorySchema()
        part_category, errors = schema.load(request.json)
        if errors:
            return errors, 422

        part_category.created_by = get_jwt_identity()

        if PartCategory.get(name=part_category.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(part_category)
        db.session.commit()

        return {"msg": "part_category created", "part_category": schema.dump(part_category).data}, 201
