from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Role


class RoleSchema(ma.ModelSchema):
    class Meta:
        model = Role
        sqla_session = db.session


class RoleResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, role_id):
        schema = RoleSchema()
        role = Role.query.get_or_404(role_id)
        return {"role": schema.dump(role).data}

    def put(self, role_id):
        schema = RoleSchema(partial=True)
        role = Role.query.get_or_404(role_id)
        role, errors = schema.load(request.json, instance=role)
        if errors:
            return errors, 422
        role.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "role updated", "role": schema.dump(role).data}

    def delete(self, role_id):
        role = Role.query.get_or_404(role_id)
        db.session.delete(role)
        db.session.commit()

        return {"msg": "role deleted"}


class RoleList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = RoleSchema(many=True)
        if request.args.get("category") is not None:
            category = request.args.get("category")
            query = Role.query.filter_by(category=category)
        else:
            query = Role.query
        return paginate(query, schema)

    def post(self):
        schema = RoleSchema()
        role, errors = schema.load(request.json)
        if errors:
            return errors, 422

        role.created_by = get_jwt_identity()

        if Role.get(rolename=role.name):
            return {"msg": "The supplied rolename already exists"}, 409

        db.session.add(role)
        db.session.commit()

        return {"msg": "role created", "role": schema.dump(role).data}, 201
