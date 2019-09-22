from flask import current_app as app
from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.credit_mixin import CreditMixin
from autoshop.models.entity import Entity
from autoshop.models.item import ItemLog
from autoshop.models.entry import Entry
from autoshop.commons.util import commas
from autoshop.models.expenditure import Expenditure

class LocalPurchaseOrder(db.Model, BaseMixin, AuditableMixin, CreditMixin):
    """Basic LPO model
    """

    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    vendor_id = db.Column(db.String(50), db.ForeignKey("vendor.uuid"), nullable=False)
    amount = db.Column(db.String(50), default='0')
    narration = db.Column(db.String(50))
    status = db.Column(db.String(50), default='PENDING') 

    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')

    def __init__(self, **kwargs):
        super(LocalPurchaseOrder, self).__init__(**kwargs)
        if self.pay_type == 'credit':
            self.on_credit = True
            self.credit_status = 'PENDING'
        self.get_uuid()

    def __repr__(self):
        return "<LocalPurchaseOrder %s>" % self.uuid


    @property
    def items(self):
        return LpoItem.query.filter_by(order_id=self.uuid).count()

    
    def log_items(self):
        logs = []
        # entries = []
        items = LpoItem.query.filter_by(order_id=self.uuid).all()

        if not items:
            raise Exception("No items found in LPO. Please add some items")

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
            total += int(log.amount)

        self.amount = total

        if not Expenditure.get(uuid=self.uuid):
            db.session.add_all(logs)
            db.session.commit()

            Expenditure.init_lpo(self)

    def clear_credit(self, amount_to_pay):
        """Check if expenses on credit are cleared"""
        if not self.on_credit:
            return

        paid = self.credit['paid']
        actual_bal = self.credit['balance']
        count = self.credit['payments']

        balance = float(self.amount) - (float(paid) + float(amount_to_pay))
        
        self.credit_status = 'PAID' if int(balance) == 0 else 'PARTIAL'
        

        if balance < 0.0:
            raise Exception('Amount to pay should not be greater than the balance {2}'.format(commas(actual_bal)))
        else:
            exp = Expenditure.get(reference=self.uuid)
            exp.amount = amount_to_pay
            exp.pay_type = self.pay_type
            entry = Entry.init_expenditure(exp)
            entry.reference = self.uuid + str(count)
            entry.transact() 




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
