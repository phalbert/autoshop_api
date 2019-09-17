from flask_jwt_extended import get_jwt_identity

from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin


class Expense(db.Model, BaseMixin, AuditableMixin):
    """Expense model
    """

    item = db.Column(db.String(80))
    reference = db.Column(db.String(50))
    amount = db.Column(db.String(50))
    pay_type = db.Column(db.String(50))
    on_credit = db.Column(db.Boolean, default=False)
    credit_status = db.Column(db.String(50), default='NONE')
    narration = db.Column(db.String(4000))
    entity_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(Expense, self).__init__(**kwargs)
        if self.pay_type == 'credit':
            self.on_credit = True
            self.credit_status = 'PENDING'

        self.get_uuid()

    def __repr__(self):
        return "<Expense %s>" % self.name
