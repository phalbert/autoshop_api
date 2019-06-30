from flask_jwt_extended import get_jwt_identity
from sqlalchemy import CheckConstraint

from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.commons.dbaccess import query

class PartCategory(db.Model, BaseMixin, AuditableMixin):
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    parent_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(PartCategory, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<PartCategory %s>" % self.name
 
    @property
    def parent(self):
        if self.parent_id and self.parent_id != '0':
            return PartCategory.get(uuid=self.parent_id).name
        else:
            return None

class Part(db.Model, BaseMixin, AuditableMixin):
    """Inventory model
    """
    code = db.Column(db.String(200), nullable=False) # part number
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    category_id = db.Column(db.String(50), db.ForeignKey('part_category.uuid'))
    model_id = db.Column(db.String(50))
    price = db.Column(db.String(50))
    make_id = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    vendor_id = db.Column(db.String(50), db.ForeignKey('vendor.uuid'))
    vendor_price = db.Column(db.String(50))
    
    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')
    category = db.relationship('PartCategory')

    def __init__(self, **kwargs):
        super(Part, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Part %s>" % self.name

    def increase(self, value=1):
        self.quantity = self.quantity + value
        return self.save()    

    def descrease(self, value=1):
        self.quantity = self.quantity + value
        return self.save()  


class PartLog(db.Model, BaseMixin, AuditableMixin):
    """Inventory log model to track usage

    If a purchase is made, debit is vendor id and credit is part id
    if a sale is mafe, debit is part id and credit is entity_id
    """
    
    part_id = db.Column(db.String(50), db.ForeignKey('part.uuid'))
    reference = db.Column(db.String(50)) # job id or vendor id
    category = db.Column(db.String(50)) # sale or purchase
    credit = db.Column(db.String(50)) 
    debit = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    unit_cost = db.Column(db.String(50))
    amount = db.Column(db.Numeric(20, 2), CheckConstraint("amount > 0.0"))
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    accounting_date = db.Column(db.Date, default=db.func.now())
    accounting_period = db.Column(db.String(50), default=db.func.now())
    
    entity = db.relationship('Entity')
    part = db.relationship('Part')

    def __init__(self, **kwargs):
        super(PartLog, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<PartLog %s>" % self.part_id
    
    @property
    def debit_account(self):
        sql = (
            """ name FROM part_accounts where part_accounts.uuid ='"""
            + str(self.debit) + """'
            """
        )

        data = query(sql)
        return data if data is None else data[0]["name"]

    @property
    def credit_account(self):

        sql = (
            """ name FROM part_accounts where part_accounts.uuid ='"""
             + str(self.credit) + """'"""
        )

        data = query(sql)
        return data if data is None else data[0]["name"]
