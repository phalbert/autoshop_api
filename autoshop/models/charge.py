from sqlalchemy import and_
from sqlalchemy.ext.declarative import declared_attr

from autoshop.extensions import db
from autoshop.models import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin


class Tarriff(db.Model, BaseMixin, AuditableMixin):
    """Tarriff model : Contains charges
    """

    name = db.Column(db.String(50))
    entity_id = db.Column(db.String(50))
    tran_type = db.Column(db.String(50))
    payment_type = db.Column(db.String(50))  # [flat,percentage,tiered]
    charges = db.relationship("Charge", cascade="all, delete-orphan", lazy="dynamic")
    splits = db.relationship(
        "ChargeSplit", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, **kwargs):
        super(Tarriff, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Tarriff %s>" % self.name


class ChargeBase(db.Model, BaseMixin, AuditableMixin):
    # tell SQLAlchemy that it is abstract
    __abstract__ = True

    @declared_attr
    def code(cls):
        return db.Column(
            db.String(50), db.ForeignKey("tarriff.uuid"), nullable=False
        )  # tarriff code

    def save(self):
        """Save an object in the database."""
        try:
            # db.session.session.expire_on_commit = False
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }

    def update(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }

    def tarriff(self):
        """Get the tarriff."""
        return Tarriff.query.filter_by(uuid=self.code).first().name


class Charge(ChargeBase):
    """A Charge is a part of a tarriff
    """

    min_value = db.Column(db.BigInteger)
    max_value = db.Column(db.BigInteger)
    amount = db.Column(db.String(50))
    charge_type = db.Column(db.String(50))  # [flat,percentage]

    def __init__(self, **kwargs):
        super(Charge, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Charge %s>" % self.code


class ChargeSplit(ChargeBase):
    """Charge split model describes how a charge is shared
    """

    account_code = db.Column(db.String(50))
    percentage = db.Column(db.Numeric(18, 11))

    def __init__(self, **kwargs):
        super(ChargeSplit, self).__init__(**kwargs)

    def __repr__(self):
        return "<ChargeSplit %s>" % self.account_code
        self.get_uuid()

    def account_name(self):
        """Get the tarriff."""
        return Account.get(uuid=self.account_code).name


def get_charge_fee(chargecode, amount):
    query = Charge.query.filter(
        and_(
            Charge.code == chargecode,
            Charge.min_value <= amount,
            Charge.max_value >= amount,
        )
    ).first()

    if query.charge_type == "percentage":
        return (int(query.amount) / 100) * int(amount)
    else:
        return query.amount
