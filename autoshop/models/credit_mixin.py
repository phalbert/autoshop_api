from autoshop.extensions import db
from autoshop.models.entry import Entry
from autoshop.commons.util import commas

class CreditMixin:
    """Credit resusable components"""
    
    pay_type = db.Column(db.String(50))
    on_credit = db.Column(db.Boolean, default=False)
    credit_status = db.Column(db.String(50), default='NONE')

    def __init__(self, target_type, target_id, action, state_before, state_after):
        self.account_code = None
        self.tran_type = None

        if self.pay_type == 'credit':
            self.on_credit = True
            self.credit_status = 'PENDING'

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

        if balance < 0.0:
            raise Exception('Amount to pay should not be greater than the balance {2}'.format(commas(actual_bal)))
        else:
            entry = Entry.init_expense(self)
            entry.amount = amount_to_pay
            entry.reference = self.uuid + str(count)
            entry.transact()


