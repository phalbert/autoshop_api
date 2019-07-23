#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from datetime import datetime, timezone

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Job, Employee, ServiceRequest

from autoshop.api.resources.service_request import ServiceRequestSchema
from autoshop.api.resources.employee import EmployeeSchema
from autoshop.api.resources.entity import EntitySchema


class JobSchema(ma.ModelSchema):

    request = ma.Nested(ServiceRequestSchema)
    employee = ma.Nested(EmployeeSchema, only=('name', 'address',
                                               'email', 'phone'))
    entity = ma.Nested(EntitySchema, only=('name', 'address', 'email',
                                           'phone'))

    employee_id = ma.String(required=True)
    request_id = ma.String(required=True)
    entity_id = ma.String()
    is_complete = ma.Boolean()

    class Meta:

        model = Job
        sqla_session = db.session
        
        additional = ("creator", "time")

class JobResource(Resource):

    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, job_id):
        schema = JobSchema()
        job = Job.query.get_or_404(job_id)
        return {'job': schema.dump(job).data}

    def put(self, job_id):
        identity = get_jwt_identity()

        schema = JobSchema(partial=True)
        job = Job.query.get_or_404(job_id)
        (job, errors) = schema.load(request.json, instance=job)
        if errors:
            return (errors, 422)

        job.modified_by = identity
        if job.is_complete:
            job.completed_date = datetime.now(timezone.utc)
            job.complete()

        try:
            db.session.commit()
            return {'msg': 'job updated', 'job': schema.dump(job).data}
        except Exception as e:
            db.session.rollback()
            return ({'msg': 'post error', 'exception': e.args}, 500)

    def delete(self, job_id):
        job = Job.query.get_or_404(job_id)
        db.session.delete(job)
        db.session.commit()

        return {'msg': 'job deleted'}


class JobList(Resource):

    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = JobSchema(many=True)
        jobcode = request.args.get('code')
        if jobcode is not None:
            query = Job.query.filter_by(uuid=jobcode)
        elif request.args.get('entity'):
            query = \
                Job.query.filter_by(entity_id=request.args.get('entity'
                                                               ))
        elif request.args.get('employee'):
            query = \
                Job.query.filter_by(employee_id=request.args.get('employee'
                                                                 ))
        elif request.args.get('request'):
            query = \
                Job.query.filter_by(request_id=request.args.get('request'
                                                                ))
        else:
            query = Job.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = JobSchema()
        (job, errors) = schema.load(request.json)
        if errors:
            return (errors, 422)

        job.created_by = identity

        try:
            employee = Employee.get(uuid=job.employee_id)
            if not employee:
                return ({'msg': 'Employee id supplied not found'}, 422)
            if not ServiceRequest.get(uuid=job.request_id):
                return ({'msg': 'The service request id supplied not found'
                         }, 422)
            if Job.get(request_id=job.request_id):
                return ({'msg': 'A job already exists for this service request'
                         }, 409)

            job.entity_id = employee.entity_id

            db.session.add(job)
            db.session.commit()
            return ({'msg': 'job created',
                     'job': schema.dump(job).data}, 201)
        except Exception as e:

            db.session.rollback()

            return ({'msg': e.args[0], 'exception': e.args}, 500)
