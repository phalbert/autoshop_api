from flask import request, current_app as app
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Employee, Entity, EmployeeType


class EmployeeSchema(ma.ModelSchema):

    type_id = ma.String(required=True)
    entity_id = ma.String(required=True)
    name = ma.String(required=True)
    email = ma.Email()
    address = ma.String(required=True)
    phone = ma.String(
        validate=[
            validate.Regexp(
                r"^(256|0)[3,4,7][0,1,5,7,8,9][0-9]{7}$",
                error="Invalid phone number supplied",
            )
        ],
        required=True,
    )

    class Meta:
        model = Employee
        sqla_session = db.session

        additional = ("entity",)


class EmployeeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, employee_id):
        schema = EmployeeSchema()
        employee = Employee.query.get_or_404(employee_id)
        return {"employee": schema.dump(employee).data}

    def put(self, employee_id):
        schema = EmployeeSchema(partial=True)
        employee = Employee.query.get_or_404(employee_id)
        employee, errors = schema.load(request.json, instance=employee)
        if errors:
            return errors, 422
        employee.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "employee updated", "employee": schema.dump(employee).data}

    def delete(self, employee_id):
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        return {"msg": "employee deleted"}


class EmployeeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = EmployeeSchema(many=True)

        if request.args.get("entity") and request.args.get("phone"):
            query = Employee.query.filter_by(
                entity_id=request.args.get("entity"), phone=request.args.get("phone")
            )
        elif request.args.get("entity") is not None:
            query = Employee.query.filter_by(entity_id=request.args.get("entity"))
        elif request.args.get("phone") is not None:
            query = Employee.query.filter_by(phone=request.args.get("phone"))
        if request.args.get("uuid") is not None:
            query = Employee.query.filter_by(uuid=request.args.get("uuid"))
        else:
            query = Employee.query

        return paginate(query.order_by(Employee.id.desc()), schema)

    def post(self):
        try:
            schema = EmployeeSchema()
            employee, errors = schema.load(request.json)
            if errors:
                return errors, 422

            if not employee.created_by:
                employee.created_by = get_jwt_identity()
            app.logger.info(employee.entity_id)

            if not Entity.get(uuid=employee.entity_id):
                return {"msg": "The supplied entity id does not exist"}, 422
            if not EmployeeType.get(
                uuid=employee.type_id, entity_id=employee.entity_id
            ):
                return {"msg": "The supplied employee type does not exist"}, 422
            if Employee.get(phone=employee.phone, entity_id=employee.entity_id):
                return {"msg": "The supplied employee phone already exists"}, 409
            else:

                db.session.add(employee)
                db.session.commit()

            return (
                {"msg": "employee created", "employee": schema.dump(employee).data},
                201,
            )

        except Exception as e:
            return {"msg": e.args}, 500
