from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Setting


class SettingSchema(ma.ModelSchema):
    class Meta:
        model = Setting
        sqla_session = db.session

        additional = ("creator",)


class SettingResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, setting_id):
        schema = SettingSchema()
        setting = Setting.query.get_or_404(setting_id)
        return {"setting": schema.dump(setting).data}

    def put(self, setting_id):
        schema = SettingSchema(partial=True)
        setting = Setting.query.get_or_404(setting_id)
        setting, errors = schema.load(request.json, instance=setting)
        if errors:
            return errors, 422
        setting.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "setting updated", "setting": schema.dump(setting).data}

    def delete(self, setting_id):
        setting = Setting.query.get_or_404(setting_id)
        db.session.delete(setting)
        db.session.commit()

        return {"msg": "setting deleted"}


class SettingList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = SettingSchema(many=True)
        query = Setting.query
        return paginate(query, schema)

    def post(self):
        schema = SettingSchema()
        setting, errors = schema.load(request.json)
        if errors:
            return errors, 422

        setting.created_by = get_jwt_identity()

        if Setting.get(name=setting.name):
            return {"msg": "The supplied name already exists"}, 409

        db.session.add(setting)
        db.session.commit()

        return {"msg": "setting created", "setting": schema.dump(setting).data}, 201
