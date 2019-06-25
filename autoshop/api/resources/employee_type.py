from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import EmployeeType, Entity


class EmployeeTypeSchema(ma.ModelSchema):

    entity_id = ma.String(required=True)

    class Meta:
        model = EmployeeType
        sqla_session = db.session

        additional = ("creator",)


class EmployeeTypeResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, employee_type_id):
        schema = EmployeeTypeSchema()
        employee_type = EmployeeType.query.get_or_404(employee_type_id)
        return {"employee_type": schema.dump(employee_type).data}

    def put(self, employee_type_id):
        schema = EmployeeTypeSchema(partial=True)
        employee_type = EmployeeType.query.get_or_404(employee_type_id)
        employee_type, errors = schema.load(request.json, instance=employee_type)
        if errors:
            return errors, 422
        employee_type.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "employee_type updated",
            "employee_type": schema.dump(employee_type).data,
        }

    def delete(self, employee_type_id):
        employee_type = EmployeeType.query.get_or_404(employee_type_id)
        db.session.delete(employee_type)
        db.session.commit()

        return {"msg": "employee_type deleted"}


class SubEmployeeTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self, parent_id):
        schema = EmployeeTypeSchema(many=True)

        if request.args.get("entity") is not None:
            company = request.args.get("entity")
            query = EmployeeType.query.filter_by(entity_id=company)
        else:
            query = EmployeeType.query.filter_by(parent_id=parent_id).all()
        return schema.dump(query).data


class EmployeeTypeList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = EmployeeTypeSchema(many=True)

        if request.args.get("entity") is not None:
            company = request.args.get("entity")
            query = EmployeeType.query.filter_by(entity_id=company)
        elif request.args.get("uuid") is not None:
            uuid = request.args.get("uuid")
            query = EmployeeType.query.filter_by(uuid=uuid)
        else:
            query = EmployeeType.query
        return paginate(query, schema)

    def post(self):
        schema = EmployeeTypeSchema()
        employee_type, errors = schema.load(request.json)
        if errors:
            return errors, 422

        try:
            employee_type.created_by = get_jwt_identity()
            
            if not Entity.get(uuid=employee_type.entity_id):
                return {"msg": "Entity not found"}, 422
            if EmployeeType.get(
                name=employee_type.name, entity_id=employee_type.entity_id
            ):
                return {"msg": "The supplied employee_type already exists"}, 409
            else:
                db.session.add(employee_type)
            db.session.commit()

            return (
                {
                    "msg": "employee_type created",
                    "employee_type": schema.dump(employee_type).data,
                },
                201,
            )
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, 500
