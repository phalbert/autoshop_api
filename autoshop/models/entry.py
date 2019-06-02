from datetime import datetime

from sqlalchemy import CheckConstraint

from autoshop.commons.dbaccess import query
from autoshop.extensions import db
from autoshop.models import Account, Entity
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.charge import ChargeSplit, Tarriff, get_charge_fee


class Entry(db.Model):
    """Ledger model
    An entry is a record of movement of value between accounts
    """

    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(20, 2), CheckConstraint("amount > 0.0"))
    debit = db.Column(db.Integer, db.ForeignKey("accounts.id", ondelete="RESTRICT"))
    credit = db.Column(db.Integer, db.ForeignKey("accounts.id", ondelete="RESTRICT"))
    tran_type = db.Column(db.String(50))
    phone = db.Column(db.String(50))
    pay_type = db.Column(db.String(50))
    description = db.Column(db.String(4000))
    cheque_number = db.Column(db.String(80))
    entity_id = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    accounting_date = db.Column(db.Date, default=db.func.now())
    accounting_period = db.Column(db.String(50), default=db.func.now())

    def __init__(self, **kwargs):
        super(Entry, self).__init__(**kwargs)
        self.accounting_period = datetime.now().strftime("%Y-%m")

    def __repr__(self):
        return "<Entry %s>" % self.reference

    @property
    def entity(self):
        return Entity.get(uuid=self.entity_id).name

    @property
    def debit_account(self):
        """
        Get the limits per category..
        this is the summation of all entries under a category
        """
        sql = (
            """ name FROM accounts INNER JOIN account_holders on
            account_holders.uuid=accounts.owner_id where accounts.id = """
            + str(self.debit) + """
            """
        )

        data = query(sql)
        return data if data is None else data[0]["name"]

    @property
    def credit_account(self):
        """
        Get the limits per category..
        this is the summation of all entries under a category
        """
        sql = (
            """ name FROM accounts INNER JOIN account_holders on
            account_holders.uuid=accounts.owner_id where accounts.id =
            """ + str(self.credit) + """ """
        )

        data = query(sql)
        return data if data is None else data[0]["name"]

    def save(self):
        """Save an object in the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }

    def serialize(self):
        """Convert sqlalchemy object to python dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    @classmethod
    def get(cls, **kwargs):
        """Get a specific object from the database."""
        return cls.query.filter_by(**kwargs).first()

    def get_entries(self):
        entries = [self]
        charge = Tarriff.get(
            tran_type=self.tran_type, payment_type=self.pay_type, entity_id="ALL"
        )

        if charge:
            charge_fee = get_charge_fee(charge.code, self.amount)

            splits = ChargeSplit.query.filter_by(code=charge.code).all()

            for split in splits:
                name = "charge-" + str(splits.index(split) + 1)
                fee = float(split.percentage / 100) * float(charge_fee)

                e = Entry(
                    reference=self.reference,
                    amount=fee,
                    debit=self.debit,
                    credit=Account.get(code=split.account_code).id,
                    description=charge.name,
                    tran_type="charge",
                    phone=self.phone,
                    pay_type=self.pay_type,
                    utility_code=name,
                    entity_id=self.entity_id,
                )
                entries.append(e)

        return entries

    def transact(self):
        entries = self.get_entries()
        for entr in entries:
            db.session.add(entr)
        db.session.commit()

        if self.phone:
            self.sms(self.phone)

    def sms(self, phone):
        try:
            from autoshop.commons.messaging import send_sms_async

            if self.tran_type == "payment":
                msg = (
                    "Hello "
                    + Account.get(id=self.credit).name
                    + ", your payment of UGX "
                    + "{:,}".format(float(self.amount))
                    + " has been received "
                )
            else:
                msg = (
                    "Hello "
                    + Account.get(id=self.debit).name
                    + ", please note that you have a bill of UGX "
                    + "{:,}".format(float(self.amount))
                    + ". "
                )

            send_sms_async(phone, msg)
        except Exception:
            pass


class Transaction(db.Model, BaseMixin, AuditableMixin):
    tranid = db.Column(db.String(50))
    reference = db.Column(db.String(50))
    vendor_id = db.Column(db.String(50))
    phone = db.Column(db.String(50))
    category = db.Column(db.String(50))
    tran_type = db.Column(db.String(50))
    pay_type = db.Column(db.String(50))
    amount = db.Column(db.String(50))
    narration = db.Column(db.String(200))
    status = db.Column(db.String(50), default="PENDING")
    status_id = db.Column(db.String(50))
    reason = db.Column(db.String(4000))
    entity_id = db.Column(db.String(50))
    is_synchronous = db.Column(db.Boolean, default=False)
    processed = db.Column(db.Boolean, default=False)
    reconciled = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Transaction %s>" % self.uuid
