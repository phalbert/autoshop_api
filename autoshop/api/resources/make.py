from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Make


class MakeSchema(ma.ModelSchema):
    class Meta:
        model = Make
        sqla_session = db.session

        additional = ("creator",)


class MakeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, make_id):
        schema = MakeSchema()
        make = Make.query.get_or_404(make_id)
        return {"make": schema.dump(make).data}

    def put(self, make_id):
        schema = MakeSchema(partial=True)
        make = Make.query.get_or_404(make_id)
        make, errors = schema.load(request.json, instance=make)
        if errors:
            return errors, 422

        return {
            "msg": "make updated",
            "make": schema.dump(make).data,
        }

    def delete(self, make_id):
        make = Make.query.get_or_404(make_id)
        db.session.delete(make)
        db.session.commit()

        return {"msg": "make deleted"}


class MakeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = MakeSchema(many=True)
        query = Make.query
        return paginate(query, schema)

    def post(self):
        schema = MakeSchema()
        make, errors = schema.load(request.json)
        if errors:
            return errors, 422

        make.created_by = get_jwt_identity()

        if Make.get(name=make.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(make)
        db.session.commit()

        return (
            {
                "msg": "make created",
                "make": schema.dump(make).data,
            },
            201,
        )
