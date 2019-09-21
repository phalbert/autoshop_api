from flask import current_app as app

from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entry import Entry
from autoshop.commons.util import commas

class Expenditure(db.Model, BaseMixin, AuditableMixin):
    """Expenditure model: expenses, purchases, payouts, salaries etc
    """
    reference = db.Column(db.String(50))
    amount = db.Column(db.String(50))
    phone = db.Column(db.String(80))
    pay_type = db.Column(db.String(50))
    on_credit = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    credit_status = db.Column(db.String(50), default='NONE')
    narration = db.Column(db.String(4000))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    vendor_id = db.Column(db.String(50), db.ForeignKey("vendor.uuid"), nullable=False)
    
    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')

    def __init__(self, **kwargs):
        super(Expenditure, self).__init__(**kwargs)
        if self.pay_type == 'credit':
            self.on_credit = True
            self.credit_status = 'PENDING'

        self.get_uuid()

    def __repr__(self):
        return "<Expenditure of {0} on {1}>".format(self.amount, self.item)
 
    @property
    def credit(self):
        entries = Entry.query.filter_by(cheque_number=self.reference).all()
        count = 0
        paid = 0
        for entry in entries:
            if 'credit' not in entry.reference:
                paid += entry.amount
                count += 1

        return {
            "paid": float(paid),
            "balance": float(self.amount) - float(paid),
            "payments": count
        }

    def clear_credit(self, amount_to_pay):
        """Check if expenses on credit are cleared"""
        if not self.on_credit:
            raise Exception('This is not a credit expense')

        paid = self.credit['paid']
        actual_bal = self.credit['balance']
        count = self.credit['payments']

        balance = float(self.amount) - (float(paid) + float(amount_to_pay))
        
        self.credit_status = 'PAID' if int(balance) == 0 else 'PARTIAL'
        app.logger.info(self.credit_status)

        if balance < 0.0:
            raise Exception('Amount to pay should not be greater than the balance {2}'.format(commas(actual_bal)))
        else:
            entry = Entry.init_expenditure(self)
            entry.amount = amount_to_pay
            entry.reference = self.uuid + str(count)
            entry.transact()
    
    @staticmethod
    def init_lpo(lpo):
        exp = Expenditure(
            reference=lpo.uuid,
            amount=lpo.amount,
            phone='',
            pay_type=lpo.pay_type,
            category='purchase',
            narration=lpo.narration,
            entity_id=lpo.entity_id,
            vendor_id=lpo.vendor_id
        )
        exp.create()

    def create(self):
        entry = Entry.init_expenditure(self)
        self.save()
        entry.transact()
