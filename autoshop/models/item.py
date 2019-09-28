import datetime
from sqlalchemy import CheckConstraint
from flask import current_app as app

from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.commons.dbaccess import query
from autoshop.commons.util import commas

class ItemCategory(db.Model, BaseMixin, AuditableMixin):
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    parent_id = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    entity = db.relationship("Entity")

    def __init__(self, **kwargs):
        super(ItemCategory, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<ItemCategory %s>" % self.name

    @property
    def parent(self):
        if self.parent_id and self.parent_id != "0":
            return ItemCategory.get(uuid=self.parent_id).name
        else:
            return None


class Item(db.Model, BaseMixin, AuditableMixin):
    """Inventory model
    """

    code = db.Column(db.String(200), nullable=False)  # item number
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    category_id = db.Column(db.String(50), db.ForeignKey("item_category.uuid"))
    model_id = db.Column(db.String(50))
    price = db.Column(db.String(50))
    item_type = db.Column(db.String(50))
    make_id = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    entity = db.relationship("Entity")
    category = db.relationship("ItemCategory")

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Item %s>" % self.name

    @property
    def quantity(self):
        """Get the item balance."""
        try:
            return query(
                " quantity from item_balances where uuid='" + str(self.uuid) + "'"
            )[0]["quantity"]
        except Exception:
            return 0


class ItemLog(db.Model, BaseMixin, AuditableMixin):
    """Inventory log model to track usage

    If a purchase is made, debit is vendor id and credit is item id
    if a sale is mafe, debit is item id and credit is entity_id
    """

    item_id = db.Column(db.String(50), db.ForeignKey("item.uuid"))
    reference = db.Column(db.String(50))  # job id or vendor id
    category = db.Column(db.String(50))  # sale or purchase
    credit = db.Column(db.String(50))
    debit = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    unit_cost = db.Column(db.String(50))
    pay_type = db.Column(db.String(50))
    on_credit = db.Column(db.Boolean, default=False)
    credit_status = db.Column(db.String(50), default='NONE')
    amount = db.Column(db.Numeric(20, 2), CheckConstraint("amount > 0.0"))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))
    accounting_date = db.Column(db.Date, default=db.func.now())
    accounting_period = db.Column(db.String(50), default=db.func.now())

    entity = db.relationship("Entity")
    item = db.relationship("Item")

    def __init__(self, **kwargs):
        super(ItemLog, self).__init__(**kwargs)
        self.accounting_period = datetime.now().strftime("%Y-%m")
        self.get_uuid()

    def __repr__(self):
        return "<ItemLog %s>" % self.item_id

    @property
    def debit_account(self):
        sql = (
            """ name FROM item_accounts where item_accounts.uuid ='"""
            + str(self.debit)
            + """'
            """
        )

        data = query(sql)
        return data if data is None else data[0]["name"]

    @property
    def credit_account(self):

        sql = (
            """ name FROM item_accounts where item_accounts.uuid ='"""
            + str(self.credit)
            + """'"""
        )

        data = query(sql)
        return data if data is None else data[0]["name"]

    def is_valid(self):
        """validate the object"""

        if self.category not in ('sale', 'purchase'):
            return False, {"msg": "The category {0} doesn't exist".format(self.tran_type)}, 422
        if not Item.get(uuid=self.credit) and not Item.get(uuid=self.debit):
            return False, {"msg": "The supplied item id does not exist"}, 422
        if ItemLog.get(reference=self.reference):
            return False, {"msg": "The supplied reference already exists"}, 409
        if ItemLog.get(reference=self.cheque_number):
            return False, {"msg": "This transaction is already reversed"}, 409
        if self.category == "reversal" and not ItemLog.get(
                reference=self.cheque_number
        ):
            return False, {"msg": "You can only reverse an existing transaction"}, 422

        # check balance
        item = Item.get(uuid=self.debit)
        bal_after = int(item.quantity) - int(self.quantity)
        app.logger.info(item.quantity, self.quantity)

        if Item.get(uuid=self.item_id).name != 'labour' and self.category == 'sale' and float(bal_after) < 0.0:
            return False, {
                "msg": "Insufficient quantity on the {0} account {1}".format(item.name, commas(item.quantity))}, 409

        if self.tran_type == "reversal":
            orig = ItemLog.get(reference=self.cheque_number)
            self.debit = orig.credit
            self.credit = orig.debit
            self.amount = orig.amount
            self.entity_id = orig.entity_id

        return True, self, 200

    @staticmethod
    def init_jobitem(job_item):
        item_log = ItemLog(
            item_id=job_item.item_id,
            debit=job_item.item_id,
            credit=job_item.entity_id,
            reference=job_item.job_id,
            category='sale',
            quantity=job_item.quantity,
            amount=job_item.cost,
            unit_cost=job_item.unit_cost,
            entity_id=job_item.entity_id,
        )
        valid, reason, status = item_log.is_valid()
        if not valid:
            raise Exception(reason.get('msg'), status)
        return item_log

    def transact(self):
        """
        :rtype: object
        If a customer is invoiced, value is debited off their account onto
        the entity account, when they make a payment
        1. Value is debited off the `escrow` onto the customer account
        2. Value is also moved off the entity account onto the pay type account

        In the future, the payment type account ought to be created per entity
        """
        valid, reason, status = self.is_valid()
        if not valid:
            raise Exception(reason.get('msg'), status)

        db.session.commit()
