#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import validate

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import JobItem, Job, PartLog
from autoshop.api.resources.job import JobSchema


class JobItemSchema(ma.ModelSchema):

    job = ma.Nested(JobSchema, only=('id', 'employee_id', 'request_id',
                                     'is_complete'))
    not_empty = validate.Length(min=1, max=50,
                                error='Field cant be empty.')

    job_id = ma.String(required=True)
    item = ma.String(required=True, validate=[not_empty])
    quantity = ma.Integer(required=True)
    unit_cost = ma.Integer(required=True)
    entity_id = ma.String(required=True)

    class Meta:

        model = JobItem
        sqla_session = db.session

        additional = ('creator', 'cost')


class JobItemResource(Resource):

    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, job_item_id):
        schema = JobItemSchema()
        job_item = JobItem.query.get_or_404(job_item_id)
        return {'job_item': schema.dump(job_item).data}

    def put(self, job_item_id):
        identity = get_jwt_identity()

        schema = JobItemSchema(partial=True)
        job_item = JobItem.query.get_or_404(job_item_id)
        (job_item, errors) = schema.load(request.json,
                                         instance=job_item)
        if errors:
            return (errors, 422)

        job_item.modified_by = identity

        try:
            db.session.commit()
            return {'msg': 'job_item updated',
                    'job_item': schema.dump(job_item).data}
        except Exception as e:
            db.session.rollback()
            return ({'msg': 'post error', 'exception': e.args}, 500)

    def delete(self, job_item_id):
        job_item = JobItem.query.get_or_404(job_item_id)
        db.session.delete(job_item)
        db.session.commit()

        return {'msg': 'job_item deleted'}


class JobItemList(Resource):

    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = JobItemSchema(many=True)
        code = request.args.get('code')
        request.args.get('amount')

        if code:
            query = JobItem.query.filter_by(job_id=code)
        else:
            query = JobItem.query
        return paginate(query, schema)

    def post(self):
        identity = get_jwt_identity()

        schema = JobItemSchema()
        (job_item, errors) = schema.load(request.json)
        if errors:
            return (errors, 422)

        job_item.created_by = identity

        try:
            if not Job.get(uuid=job_item.job_id):
                return ({'msg': 'The supplied job code doesnt exist'},
                        422)
            if JobItem.get(job_id=job_item.job_id, item=job_item.item):
                return ({'msg': 'The supplied job_item already exists'
                         }, 409)
            else:
                part_log = PartLog(
                    part_id=job_item.item,
                    debit=job_item.item,
                    credit=job_item.entity_id,
                    reference=job_item.job_id,
                    category='sale',
                    quantity=job_item.quantity,
                    amount=job_item.cost,
                    unit_cost=job_item.unit_cost,
                    entity_id=job_item.entity_id,
                )

                db.session.add(job_item)
                db.session.add(part_log)
                db.session.commit()
                return ({'msg': 'job_item created',
                         'job_item': schema.dump(job_item).data}, 201)
        except Exception as e:
            db.session.rollback()
            return ({'msg': e.args, 'exception': e.args}, 500)
