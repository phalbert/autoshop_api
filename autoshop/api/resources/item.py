from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.commons.dbaccess import query
from autoshop.extensions import db, ma
from autoshop.models import Item, Entity, VehicleModel, ItemCategory
from autoshop.api.resources.item_category import ItemCategorySchema
from autoshop.api.resources.entity import EntitySchema
from autoshop.api.resources.vendor import VendorSchema


class ItemSchema(ma.ModelSchema):

    entity = ma.Nested(EntitySchema, only=('name', 'address', 'email', 'phone'))
    category = ma.Nested(ItemCategorySchema)
    vendor = ma.Nested(VendorSchema)

    name = ma.String(required=True)
    code = ma.String(required=True)
    model_id = ma.String(required=True)
    category_id = ma.String(required=True)
    price = ma.Integer(required=True)
    make_id = ma.Integer(required=True)
    item_type = ma.String(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = Item
        sqla_session = db.session

        additional = ("creator", "quantity")


class ItemResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, item_id):
        schema = ItemSchema()
        item = Item.query.get_or_404(item_id)
        return {"item": schema.dump(item).data}

    def put(self, item_id):
        schema = ItemSchema(partial=True)
        item = Item.query.get_or_404(item_id)
        item, errors = schema.load(request.json, instance=item)
        if errors:
            return errors, 422
        item.modified_by = get_jwt_identity()
        db.session.commit()
        return {"msg": "item updated", "item": schema.dump(item).data}

    def delete(self, item_id):
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()

        return {"msg": "item deleted"}


class ItemList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = ItemSchema(many=True)

        if request.args.get("uuid") is not None:
            query = Item.query.filter_by(uuid=request.args.get("uuid"))
        else:
            query = Item.query
        return paginate(query, schema)

    def post(self):
        schema = ItemSchema()
        item, errors = schema.load(request.json)
        if errors:
            return errors, 422

        item.created_by = get_jwt_identity()

        if not Entity.get(uuid=item.entity_id):
            return {"msg": "The supplied entity id does not exist"}, 422
        if Item.get(name=item.name):
            return {"msg": "The supplied name already exists"}, 409
        if Item.get(code=item.code):
            return {"msg": "The supplied code already exists"}, 409
        if item.model_id != 'ALL' and not VehicleModel.get(uuid=item.model_id):
            return {"msg": "The supplied vehicle model doesnt exist"}, 422
        if not ItemCategory.get(uuid=item.category_id):
            return {"msg": "The supplied item category doesnt exist"}, 422

        db.session.add(item)
        db.session.commit()

        return {"msg": "item created", "item": schema.dump(item).data}, 201


class ItemEntriesResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, item_id):
        sql = (
            """ 0 as entry_id,'credit' as tran_category,
                (select date_created from item where uuid="""
            + str(item_id)
            + """)
                as date_created,0 as quantity,0 as balance
                union
                select entry_id,tran_category,date_created,quantity,
                (select sum(quantity) from item_ledger b where account_id="""
            + str(item_id)
            + """
                and b.entry_id<=a.entry_id ) as balance from item_ledger a
                where account_id="""
            + str(item_id)
            + """
                order by entry_id desc"""
        )

        response = query(sql)
        return response, 200

class ItemEntriesList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        sql = """ V.entry_id,account_id,B.uuid,B.name, V.reference,
        V.date_created,quantity,amount, e.name as entity_id FROM item_ledger AS V
        inner join item_accounts AS B on B.uuid=V.account_id
        inner join item I on B.uuid=I.uuid
        inner join entity e on e.uuid=I.entity_id """

        if request.args.get("company") is not None:
            where = " where entity_id='" + request.args.get("company") + "'"
            sql = sql + where

        order_by = " order by V.date_created desc,  V.entry_id desc, V.amount desc"
        sql = sql + order_by

        response = query(sql)
        return response, 200
