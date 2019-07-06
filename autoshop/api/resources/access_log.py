#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from autoshop.models import AccessLog
from autoshop.extensions import ma, db
from autoshop.commons.pagination import paginate
from flask_jwt_extended import get_jwt_identity
from marshmallow import validate
from sqlalchemy import desc


class AccessLogSchema(ma.ModelSchema):

    not_empty = validate.Length(min=1, max=50,
                                error='Field cant be empty.')

    ip = ma.String(required=True, validate=[not_empty])
    url = ma.String(required=True, validate=[not_empty])
    status = ma.String(required=True, validate=[not_empty])
    country = ma.String(required=True, validate=[not_empty])

    class Meta:

        model = AccessLog
        sqla_session = db.session


class AccessLogResource(Resource):

    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, access_log_id):
        schema = AccessLogSchema()
        access_log = AccessLog.query.get_or_404(access_log_id)
        return {'access_log': schema.dump(access_log).data}


class AccessLogList(Resource):

    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = AccessLogSchema(many=True)
        access_log_code = request.args.get('code')

        if access_log_code is not None:
            query = AccessLog.query.filter_by(code=access_log_code)
        else:
            query = \
                AccessLog.query.order_by(desc(AccessLog.date_created))
        return paginate(query.order_by(AccessLog.id.desc()), schema)

    def post(self):
        identity = get_jwt_identity()

        schema = AccessLogSchema()
        (access_log, errors) = schema.load(request.json)
        if errors:
            return (errors, 422)

        access_log.created_by = identity

        try:
            access_log.save()
            return ({'msg': 'access_log created',
                     'access_log': schema.dump(access_log).data}, 201)
        except Exception as e:
            db.session.rollback()
            return ({'msg': 'post error', 'exception': e.args}, 500)
