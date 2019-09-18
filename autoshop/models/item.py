from sqlalchemy import CheckConstraint

from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.commons.dbaccess import query


class ItemCategory(db.Model, BaseMixin, AuditableMixin):
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    parent_id = db.Column(db.String(50))

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
