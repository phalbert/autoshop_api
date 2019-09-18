from flask_jwt_extended import get_jwt_identity

from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin


class Setting(db.Model, BaseMixin, AuditableMixin):
    """Setting model
    """

    name = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(4000))
    company = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(Setting, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Setting %s>" % self.name


class CustomerType(db.Model, BaseMixin, AuditableMixin):
    """"
       in fleet, out fleet
    """

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50))
    entity_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(CustomerType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<CustomerType %s>" % self.name


class TransactionType(db.Model, BaseMixin, AuditableMixin):
    """"
       claim, topup, reversal, charge, adjustment
    """

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(TransactionType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<TransactionType %s>" % self.name


class PaymentType(db.Model, BaseMixin, AuditableMixin):
    """
       Cash, Momo, Bank, e.t.c
    """

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(PaymentType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<PaymentType %s>" % self.name
    
    @property
    def account(self):
        setting = Setting.get(uuid=self.uuid)
        return Account.get(uuid=setting.value).id

    def save(self):
        account = Account(
            acc_type="commission",
            owner_id=self.uuid,
            created_by=get_jwt_identity(),
            group="system",
            minimum_balance=0.0
        )

        setting = Setting(
            uuid=self.uuid,
            name=self.name,
            value=account.uuid,
            company="ALL",
            created_by=get_jwt_identity(),
        )

        db.session.add(account)
        db.session.add(setting)
        db.session.add(self)
        db.session.commit()
