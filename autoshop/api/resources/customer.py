from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.api.resources.account import AccountSchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Customer, Entity, CustomerType


class CustomerSchema(ma.ModelSchema):

    account = ma.Nested(AccountSchema)

    entity_id = ma.String(required=True)
    name = ma.String(required=True)
    email = ma.Email()
    address = ma.String(required=True)
    phone = ma.String(
        validate=[
            validate.Regexp(
                r"^256[3,4,7][0,1,5,7,8,9][0-9]{7}$",
                error="Invalid phone number supplied",
            )
        ],
        required=True,
    )

    class Meta:
        model = Customer
        sqla_session = db.session

        additional = ("entity",)


class CustomerResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, customer_id):
        schema = CustomerSchema()
        customer = Customer.query.get_or_404(customer_id)
        return {"customer": schema.dump(customer).data}

    def put(self, customer_id):
        schema = CustomerSchema(partial=True)
        customer = Customer.query.get_or_404(customer_id)
        customer, errors = schema.load(request.json, instance=customer)
        if errors:
            return errors, 422
        customer.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "customer updated", "customer": schema.dump(customer).data}

    def delete(self, customer_id):
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()

        return {"msg": "customer deleted"}


class CustomerList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = CustomerSchema(many=True)

        if request.args.get("entity") and request.args.get("phone"):
            query = Customer.query.filter_by(
                entity_id=request.args.get("entity"), phone=request.args.get("phone")
            )
        elif request.args.get("entity") is not None:
            query = Customer.query.filter_by(entity_id=request.args.get("entity"))
        elif request.args.get("phone") is not None:
            query = Customer.query.filter_by(phone=request.args.get("phone"))
        else:
            query = Customer.query

        return paginate(query.order_by(Customer.id.desc()), schema)

    def post(self):
        try:
            schema = CustomerSchema()
            customer, errors = schema.load(request.json)
            if errors:
                return errors, 422

            if not customer.created_by:
                customer.created_by = get_jwt_identity()

            if not Entity.get(uuid=customer.entity_id):
                return {"msg": "The supplied entity id does not exist"}, 422
            if not CustomerType.get(
                uuid=customer.type_id, entity_id=customer.entity_id
            ):
                return {"msg": "The supplied customer type does not exist"}, 422
            if Customer.get(phone=customer.phone, entity_id=customer.entity_id):
                return {"msg": "The supplied customer phone already exists"}, 409
            else:
                customer.log("A")

                account = Account(
                    owner_id=customer.uuid,
                    acc_type="customer",
                    created_by=get_jwt_identity(),
                    group=customer.entity_id,
                )
                db.session.add(account)
                db.session.commit()

            return (
                {"msg": "customer created", "customer": schema.dump(customer).data},
                201,
            )

        except Exception as e:
            return {"msg": e.args}, 500
