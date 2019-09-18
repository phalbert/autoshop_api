from flask import json, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.account import AccountSchema
from autoshop.api.resources.vendor import VendorSchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Entity, Vendor


class EntitySchema(ma.ModelSchema):
    account = ma.Nested(AccountSchema)

    class Meta:
        model = Entity
        sqla_session = db.session

        additional = ("creator",)


class EntityResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, entity_id):
        schema = EntitySchema()
        entity = Entity.query.get_or_404(entity_id)
        return {"entity": schema.dump(entity).data}

    def put(self, entity_id):
        schema = EntitySchema(partial=True)
        entity = Entity.query.get_or_404(entity_id)
        entity, errors = schema.load(request.json, instance=entity)
        if errors:
            return errors, 422

        entity.modified_by = get_jwt_identity()
        db.session.commit()

        return {"msg": "entity updated", "entity": schema.dump(entity).data}

    def delete(self, entity_id):
        entity = Entity.query.get_or_404(entity_id)
        db.session.delete(entity)
        db.session.commit()

        return {"msg": "entity deleted"}


class EntityList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = EntitySchema(many=True)
        if request.args.get("uuid") is not None:
            uuid = request.args.get("uuid")
            query = Entity.query.filter_by(uuid=uuid)
        else:
            query = Entity.query
        return paginate(query.order_by(Entity.id.desc()), schema)

    def post(self):
        schema = EntitySchema()
        entity, errors = schema.load(request.json)
        if errors:
            return errors, 422

        try:

            entity.created_by = get_jwt_identity()

            if Entity.get(uuid=entity.uuid):
                return {"msg": "The supplied name already exists"}, 409
            else:
                account = Account(
                    owner_id=entity.uuid,
                    acc_type="entity",
                    created_by=get_jwt_identity(),
                    group=entity.uuid,
                )

                db.session.add(entity)
                db.session.add(account)

            db.session.commit()

            return {"msg": "entity created", "entity": schema.dump(entity).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, 500

        def batch(self):
            """Execute multiple requests, submitted as a batch. :statuscode 207: Multi status"""
            try:
                requests = json.loads(request.data)
            except ValueError as e:
                return {"msg": e}, 400

            responses = []

            for index, req in enumerate(requests):
                name = req["name"]
                email = req["email"]
                phone = req["phone"]
                address = req["address"]

                entity = Entity(
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    created_by=get_jwt_identity(),
                )
                account = Account(
                    owner_id=entity.uuid,
                    acc_type="entity",
                    created_by=get_jwt_identity(),
                    group=entity.uuid,
                    minimum_balance=0.0,
                )

                if Entity.get(name=name):
                    return {"msg": "The supplied name already exists " + name}, 409
                else:
                    db.session.add(entity)
                    db.session.add(account)

            db.session.commit()

            responses.append({"msg": "entities created"})

            return json.dumps(responses), 207


class EntityVendorResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def delete(self, entity_id, vendor_id):
        entity = Entity.query.get_or_404(entity_id)
        vendor = Vendor.query.get_or_404(vendor_id)
        entity.remove_vendor(vendor)
        db.session.commit()

        return {"msg": "partnership deleted"}


class EntityVendorList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = VendorSchema(many=True)

        if request.args.get("entity"):
            entity = Entity.get(uuid=request.args.get("entity"))
            if entity:
                query = entity.vendors.all()
            else:
                query = {}
        elif request.args.get("vendor"):
            vendor = Vendor.get(uuid=request.args.get("vendor"))
            if vendor:
                query = vendor.entities.all()
            else:
                query = {}
        else:
            from autoshop.commons.dbaccess import query

            sql = """ c.vendor_id, v.uuid as vendor_uuid, v.name as vendor,
            c.entity_id, e.uuid as entity_uuid, e.name as entity
            FROM entity_vendors c INNER JOIN entity e on e.id=c.entity_id
            INNER JOIN vendor v on v.id=c.vendor_id
            """

            data = query(sql)
            return jsonify(data)
            # return [] if data is None else data

        return schema.dump(query).data

    def post(self):
        entity_id = request.json["entity_id"]
        vendor_id = request.json["vendor_id"]

        entity = Entity.get(id=entity_id)
        vendor = Vendor.get(id=vendor_id)

        if not entity:
            return {"msg": "Entity not found"}, 422
        if not vendor:
            return {"msg": "Vendor not found"}, 422
        if entity.is_entity_vendor(vendor):
            return {"msg": "This partnership already exists"}, 409

        try:
            entity.add_vendor(vendor)
            db.session.commit()
            return {"msg": "operation successful"}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args[0]}, 500
