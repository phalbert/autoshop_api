from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.account import AccountSchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Vendor


class VendorSchema(ma.ModelSchema):
    account = ma.Nested(AccountSchema)

    class Meta:
        model = Vendor
        sqla_session = db.session

        # additional = ('creator',)


class VendorResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, vendor_id):
        schema = VendorSchema()
        vendor = Vendor.query.get_or_404(vendor_id)
        return {"vendor": schema.dump(vendor).data}

    def put(self, vendor_id):
        schema = VendorSchema(partial=True)
        vendor = Vendor.query.get_or_404(vendor_id)
        vendor, errors = schema.load(request.json, instance=vendor)
        if errors:
            return errors, 422

        vendor.modified_by = get_jwt_identity()
        db.session.commit()

        return {"msg": "vendor updated", "vendor": schema.dump(vendor).data}

    def delete(self, vendor_id):
        vendor = Vendor.query.get_or_404(vendor_id)
        db.session.delete(vendor)
        db.session.commit()

        return {"msg": "vendor deleted"}


class VendorList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = VendorSchema(many=True)
        query = Vendor.query
        return paginate(query, schema)

    def post(self):
        schema = VendorSchema()
        vendor, errors = schema.load(request.json)
        if errors:
            return errors, 422

        vendor.created_by = get_jwt_identity()

        try:
            if Vendor.get(name=vendor.name):
                return {"msg": "The supplied name already exists"}, 409
            if Vendor.get(email=vendor.email):
                return {"msg": "The supplied email already exists"}, 409

            account = Account(
                owner_id=vendor.uuid, acc_type="vendor", created_by=get_jwt_identity()
            )

            db.session.add(vendor)
            db.session.add(account)
            db.session.commit()

            return {"msg": "vendor created", "vendor": schema.dump(vendor).data}, 201
        except Exception as e:
            return {"msg": e.args}, 500
