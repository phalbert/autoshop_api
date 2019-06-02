from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from autoshop.commons.pagination import paginate
from autoshop.extensions import db, ma
from autoshop.models import Account, Customer, Entry, PaymentType, Transaction, User


class TransactionSchema(ma.ModelSchema):

    tranid = ma.String(required=True)
    reference = ma.String(required=True)
    is_synchronous = ma.String(required=True)
    amount = ma.Integer(required=True)
    narration = ma.String(required=True)
    phone = ma.String(required=True)
    tran_type = ma.String(required=True)
    pay_type = ma.String(required=True)

    class Meta:
        model = Transaction
        sqla_session = db.session

        additional = ("creator",)


class TransactionViewSchema(ma.ModelSchema):
    class Meta:
        model = Transaction
        sqla_session = db.session

        fields = (
            "tranid",
            "pay_type",
            "amount",
            "phone",
            "narration",
            "reference",
            "created_on",
        )


class TransactionResource(Resource):
    """Single object resource
    """

    method_decorators = [jwt_required]

    def get(self, transaction_id):
        schema = TransactionSchema()
        transaction = Transaction.query.get_or_404(transaction_id)
        return {"transaction": schema.dump(transaction).data}

    def put(self, transaction_id):
        schema = TransactionSchema(partial=True)
        transaction = Transaction.query.get_or_404(transaction_id)
        transaction, errors = schema.load(request.json, instance=transaction)
        if errors:
            return errors, 422
        transaction.modified_by = get_jwt_identity()
        db.session.commit()
        return {
            "msg": "transaction updated",
            "transaction": schema.dump(transaction).data,
        }

    def delete(self, transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        db.session.delete(transaction)
        db.session.commit()

        return {"msg": "transaction deleted"}


class TransactionList(Resource):
    """Creation and get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        schema = TransactionSchema(many=True)
        if request.args.get("uuid") is not None:
            uuid = request.args.get("uuid")
            query = Transaction.query.filter_by(uuid=uuid)
        elif request.args.get("company") is not None:
            company = request.args.get("company")
            query = Transaction.query.filter_by(entity_id=company)
        else:
            query = Transaction.query
        return paginate(query.order_by(Transaction.date_created.desc()), schema)

    def post(self):
        schema = TransactionSchema()
        transaction, errors = schema.load(request.json)
        if errors:
            return errors, 422

        transaction.is_synchronous = str2bool(request.json["is_synchronous"])
        transaction.created_by = get_jwt_identity()
        transaction.vendor_id = User.get(id=transaction.created_by).company_id

        if not Customer.get(uuid=transaction.reference):
            return {"msg": "This reference does not exist in our customer list"}, 422
        if Transaction.get(tranid=transaction.tranid, vendor_id=transaction.vendor_id):
            return {"msg": "The supplied transaction already exists"}, 409
        if transaction.tran_type != "payment":
            return {"msg": "Unknown transaction type supplied"}, 422
        if not PaymentType.get(uuid=transaction.pay_type):
            return {"msg": "Unknown payment type supplied"}, 422

        if transaction.is_synchronous:
            transaction.processed = True
            transaction.status = "SUCCESS"
            cust_acct = Account.get(owner_id=transaction.reference)
            transaction.entity_id = cust_acct.group
            transaction.save()

            entry = Entry(
                reference=transaction.uuid,
                debit=Account.get(owner_id=transaction.pay_type).id,
                credit=cust_acct.id,
                amount=transaction.amount,
                phone=transaction.phone,
                entity_id=transaction.entity_id,
                description=transaction.narration,
                tran_type=transaction.tran_type,
                pay_type=transaction.pay_type,
                category=transaction.category,
            )
            entry.transact()
        else:
            # just save transaction, and update later in background service
            transaction.save()

        result_schema = TransactionViewSchema()
        return (
            {
                "msg": "transaction created",
                "transaction": result_schema.dump(transaction).data,
            },
            201,
        )


def str2bool(v):
    return v.lower() in ("True", "true")
