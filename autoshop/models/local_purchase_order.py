
from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity
from autoshop.models.item import ItemLog
from autoshop.models.entry import Entry
from autoshop.commons.util import commas

class LocalPurchaseOrder(db.Model, BaseMixin, AuditableMixin):
    """Basic LPO model
    """

    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    vendor_id = db.Column(db.String(50), db.ForeignKey("vendor.uuid"), nullable=False)
    narration = db.Column(db.String(50))
    pay_type = db.Column(db.String(50))
    status = db.Column(db.String(50), default='PENDING') 

    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')

    def __init__(self, **kwargs):
        super(LocalPurchaseOrder, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<LocalPurchaseOrder %s>" % self.uuid
    
    @property
    def items(self):
        return LpoItem.query.filter_by(order_id=self.uuid).count()


    def log_items(self):
        logs = []
        entries = []
        items = LpoItem.query.filter_by(order_id=self.uuid).all()

        if not items:
            raise Exception("No items found in LPO. Please add some items")
        
        balance = Account.get(owner_id=self.pay_type).balance

        total = 0

        for item in items:
            log = ItemLog(
                item_id=item.item_id,
                debit=self.vendor_id,
                credit=item.item_id,
                reference=self.uuid,
                category='purchase',
                quantity=item.quantity,
                unit_cost=item.unit_price,
                amount=int(item.unit_price) * int(item.quantity),            
                entity_id=item.entity_id,
                pay_type=self.pay_type
            )
            logs.append(log)
            entry = Entry.init_item_log(log)
            entries.append(entry)

            total += int(log.amount)
            bal_after = int(balance) - total

            if bal_after < balance:
                raise Exception("""You do not sufficient funds on the {0} account to
            clear the LPO. Balance: {1}""".format(self.pay_type, commas(balance)) )
        

        db.session.add_all(logs)
        db.session.add_all(entries)
        db.session.commit()





class LpoItem(db.Model, BaseMixin, AuditableMixin):
    order_id = db.Column(db.String(50), db.ForeignKey('local_purchase_order.uuid'))
    item_id = db.Column(db.String(80), db.ForeignKey("item.uuid"), nullable=False)
    quantity = db.Column(db.String(50)) 
    unit_price = db.Column(db.String(50)) 
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    
    item = db.relationship('Item')
    order = db.relationship('LocalPurchaseOrder')
    entity = db.relationship('Entity')

    def __init__(self, **kwargs):
        super(LpoItem, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<LpoItem %s>" % self.uuid

    @property
    def amount(self):
        return float(self.quantity) * float(self.unit_price)
