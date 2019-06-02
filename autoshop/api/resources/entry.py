from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.api.resources.user import UserSchema
from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Entry, TransactionType, Vendor


class EntrySchema(ma.ModelSchema):
    creator = ma.Nested(UserSchema)

    debit = ma.Integer()
    credit = ma.Integer()
    reference = ma.String(required=True)
    debit = ma.String(required=True)
    credit = ma.String(required=True)
    amount = ma.Integer(required=True)
    description = ma.String(required=True)
    tran_type = ma.String(required=True)
    pay_type = ma.String(required=True)
    entity_id = ma.String(required=True)

    class Meta:
        model = Entry
        sqla_session = db.session

        additional = ("debit_account", "credit_account", "entity")


class EntryResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, entry_id):
        schema = EntrySchema()
        entry = Entry.query.get_or_404(entry_id)
        return {"entry": schema.dump(entry).data}

    def put(self, entry_id):
        schema = EntrySchema(partial=True)
        entry = Entry.query.get_or_404(entry_id)
        entry, errors = schema.load(request.json, instance=entry)
        if errors:
            return errors, 422

        return {"msg": "entry updated", "entry": schema.dump(entry).data}

    def delete(self, entry_id):
        entry = Entry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()

        return {"msg": "entry deleted"}


class EntryList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = EntrySchema(many=True)

        if request.args.get("uuid") and request.args.get("tran_type"):
            query = Entry.query.filter_by(
                entity_id=request.args.get("uuid"),
                tran_type=request.args.get("tran_type"),
            )
        elif request.args.get("uuid"):
            vendor = Vendor.get(uuid=request.args.get("uuid"))
            if vendor:
                query = Entry.query.filter_by(credit=vendor.account.id)
            else:
                query = Entry.query.filter_by(entity_id=request.args.get("uuid"))
        elif request.args.get("reference"):
            query = Entry.query.filter_by(reference=request.args.get("reference"))
        else:
            query = Entry.query
        query = query.order_by(Entry.date_created.desc(), Entry.amount.desc())
        return paginate(query, schema)

    def post(self):
        schema = EntrySchema()
        entry, errors = schema.load(request.json)
        if errors:
            return errors, 422

        entry.created_by = get_jwt_identity()
        entry.accounting_period = datetime.now().strftime("%Y-%m")

        try:
            if not TransactionType.get(uuid=entry.tran_type):
                return {"msg": "The transaction type supplied doesn't exist"}, 422
            if not Account.get(id=entry.credit) and not Account.get(id=entry.debit):
                return {"msg": "The supplied account id does not exist"}, 422
            if Entry.get(reference=entry.reference):
                return {"msg": "The supplied reference already exists"}, 409
            if Entry.get(reference=entry.cheque_number):
                return {"msg": "This transaction is already reversed"}, 409
            if entry.tran_type == "reversal" and not Entry.get(
                reference=entry.cheque_number
            ):
                return {"msg": "You can only reverse an existing transaction"}, 422

            if entry.tran_type == "reversal":
                orig = Entry.get(reference=entry.cheque_number)
                entry.debit = orig.credit
                entry.credit = orig.debit
                entry.amount = orig.amount
                entry.entity_id = orig.entity_id

            entry.transact()
            return {"msg": "entry created", "entry": schema.dump(entry).data}, 201
        except Exception as e:
            db.session.rollback()
            return {"msg": e.args, "exception": e.args}, 500
