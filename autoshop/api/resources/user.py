from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from autoshop.models import User
from autoshop.extensions import ma, db
from autoshop.commons.pagination import paginate


class UserSchema(ma.ModelSchema):

    password = ma.String(load_only=True, required=True)

    class Meta:
        model = User
        sqla_session = db.session

        additional = ("creator", "role", "company", "category")


class UserResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, user_id):
        schema = UserSchema()
        user = User.query.get_or_404(user_id)
        return {"user": schema.dump(user).data}

    def put(self, user_id):
        schema = UserSchema(partial=True)
        user = User.query.get_or_404(user_id)
        user, errors = schema.load(request.json, instance=user)
        if errors:
            return errors, 422
        user.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "user updated", "user": schema.dump(user).data}

    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}


class UserList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = UserSchema(many=True)

        if request.args.get("username") is not None:
            username = request.args.get("username")
            query = User.query.filter_by(username=username)
        elif request.args.get("company") is not None:
            company = request.args.get("company")
            query = User.query.filter_by(company_id=company)
        else:
            query = User.query
        return paginate(query.order_by(User.id.desc()), schema)

    def post(self):
        schema = UserSchema()
        user, errors = schema.load(request.json)
        if errors:
            return errors, 422

        user.created_by = get_jwt_identity()

        db.session.add(user)
        db.session.commit()

        return {"msg": "user created", "user": schema.dump(user).data}, 201
