from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import CustomerType


class CustomerTypeSchema(ma.ModelSchema):

    entity_id = ma.String(required=True)

    class Meta:
        model = CustomerType
        sqla_session = db.session

        additional = ("creator",)


class CustomerTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, customer_type_id):
        schema = CustomerTypeSchema()
        customer_type = CustomerType.query.get_or_404(customer_type_id)
        return {"customer_type": schema.dump(customer_type).data}

    def put(self, customer_type_id):
        schema = CustomerTypeSchema(partial=True)
        customer_type = CustomerType.query.get_or_404(customer_type_id)
        customer_type, errors = schema.load(request.json, instance=customer_type)
        if errors:
            return errors, 422
        customer_type.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "customer_type updated",
            "customer_type": schema.dump(customer_type).data,
        }

    def delete(self, customer_type_id):
        customer_type = CustomerType.query.get_or_404(customer_type_id)
        db.session.delete(customer_type)
        db.session.commit()

        return {"msg": "customer_type deleted"}


class SubCustomerTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self, parent_id):
        schema = CustomerTypeSchema(many=True)

        if request.args.get("entity") is not None:
            company = request.args.get("entity")
            query = CustomerType.query.filter_by(entity_id=company)
        else:
            query = CustomerType.query.filter_by(parent_id=parent_id).all()
        return schema.dump(query).data


class CustomerTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = CustomerTypeSchema(many=True)

        if request.args.get("entity") is not None:
            company = request.args.get("entity")
            query = CustomerType.query.filter_by(entity_id=company)
        elif request.args.get("uuid") is not None:
            uuid = request.args.get("uuid")
            query = CustomerType.query.filter_by(uuid=uuid)
        else:
            query = CustomerType.query
        return paginate(query, schema)

    def post(self):
        schema = CustomerTypeSchema()
        customer_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        try:
            customer_type.created_by = get_jwt_identity()

            if customer_type.get(
                name=customer_type.name, entity_id=customer_type.entity_id
            ):
                return {"msg": "The supplied customer_type already exists"}, 409
            else:
                db.session.add(customer_type)
            db.session.commit()

            return (
                {
                    "msg": "customer_type created",
                    "customer_type": schema.dump(customer_type).data,
                },
                201,
            )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, 500
