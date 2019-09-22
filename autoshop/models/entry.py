from datetime import datetime

from flask import current_app as app
from sqlalchemy import CheckConstraint

from autoshop.commons.dbaccess import query
from autoshop.commons.util import commas
from autoshop.extensions import db
from autoshop.models import Account, Entity, CommissionAccount
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.charge import ChargeSplit, Tarriff, get_charge_fee
from autoshop.models.setting import TransactionType


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
    category = db.Column(db.String(50))
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
            + str(self.debit)
            + """
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
            """
            + str(self.credit)
            + """ """
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

    def is_valid(self):
        """validate the object"""
        
        if not TransactionType.get(uuid=self.tran_type):
            return False, {"msg": "The transaction type {0} doesn't exist".format(self.tran_type)}, 422
        if not Account.get(id=self.credit) and not Account.get(id=self.debit):
            return False, {"msg": "The supplied account id does not exist"}, 422
        if Entry.get(reference=self.reference):
            return False, {"msg": "The supplied reference already exists"}, 409
        if Entry.get(reference=self.cheque_number):
            return False, {"msg": "This transaction is already reversed"}, 409
        if self.tran_type == "reversal" and not Entry.get(
                reference=self.cheque_number
            ):
            return False, {"msg": "You can only reverse an existing transaction"}, 422
        
        # check balance
        account = Account.get(id=self.debit)
        bal_after = int(account.balance) - int(self.amount)
        app.logger.info(self.amount)

        if account.minimum_balance is not None and float(bal_after) < float(account.minimum_balance):
            return False, {"msg": "Insufficient balance on {0} account {1}".format(account.name,commas(account.balance))}, 409

        if self.tran_type == "reversal":
            orig = Entry.get(tranid=self.cheque_number)
            self.debit = orig.credit
            self.credit = orig.debit
            self.amount = orig.amount
            self.entity_id = orig.entity_id

        
        return True, self, 200

    @staticmethod
    def init_expense(expense):
        entry = Entry(
            reference=expense.uuid,
            amount=expense.amount,
            phone='',
            entity_id=expense.entity_id,
            description=expense.narration,
            tran_type='expense',
            cheque_number=expense.reference,
            category=expense.item,
            pay_type=expense.pay_type,
        )
                        
        if expense.pay_type == 'credit':
            entry.debit = CommissionAccount.get(code='credit').account.id
            entry.credit = CommissionAccount.get(code='expenses').account.id
            entry.reference = entry.reference + '-credit'
        elif expense.on_credit and expense.pay_type != 'credit' and expense.credit_status in ('PAID','PARTIAL'):
            entry.debit = Account.get(owner_id=expense.pay_type).id
            entry.credit = CommissionAccount.get(code='credit').account.id
        else:
            entry.debit = Account.get(owner_id=expense.pay_type).id
            entry.credit = CommissionAccount.get(code='expenses').account.id

        valid, reason, status = entry.is_valid()
        if valid:
            return entry
        else:
            raise Exception(reason, status)

    @staticmethod
    def init_item_log(item_log):
        entry = Entry(
            reference=item_log.uuid,
            amount=item_log.amount,
            phone='',
            entity_id=item_log.entity_id,
            description=item_log.item_id,
            tran_type=item_log.category,
            category=item_log.item_id,
            pay_type=item_log.pay_type,
        )
                        
        if item_log.pay_type == 'credit':
            entry.debit = CommissionAccount.get(code='credit').account.id
            entry.credit = Account.get(owner_id=item_log.debit).id
            entry.reference = entry.reference + '-credit'
        elif item_log.on_credit and item_log.pay_type != 'credit' and item_log.credit_status == 'PAID':
            entry.debit = Account.get(owner_id=item_log.pay_type).id
            entry.credit = CommissionAccount.get(code='credit').account.id
        else:
            entry.debit = Account.get(owner_id=item_log.pay_type).id
            entry.credit = Account.get(owner_id=item_log.debit).id

        valid, reason, status = entry.is_valid()
        if valid:
            return entry
        else:
            raise Exception(reason, status)
    
    @staticmethod
    def init_expenditure(expenditure):
        entry = Entry(
            reference=expenditure.uuid,
            amount=expenditure.amount,
            phone=expenditure.phone,
            entity_id=expenditure.entity_id,
            description=expenditure.narration,
            tran_type=expenditure.category,
            cheque_number=expenditure.reference,
            category=expenditure.vendor_id,
            pay_type=expenditure.pay_type,
        )
                        
        if expenditure.pay_type == 'credit':
            entry.debit = CommissionAccount.get(code='credit').account.id
            entry.credit = CommissionAccount.get(code=expenditure.category).account.id
            entry.reference = entry.reference + '-credit'
        elif expenditure.on_credit and expenditure.pay_type != 'credit' and expenditure.credit_status in ('PAID','PARTIAL'):
            entry.debit = Account.get(owner_id=expenditure.pay_type).id
            entry.credit = CommissionAccount.get(code='credit').account.id
        else:
            entry.debit = Account.get(owner_id=expenditure.pay_type).id
            entry.credit = CommissionAccount.get(code=expenditure.category).account.id

        return entry

    @staticmethod
    def init_transaction(transaction):
        entry = Entry(
            reference=transaction.uuid,
            amount=transaction.amount,
            phone=transaction.phone,
            entity_id=transaction.entity_id,
            description=transaction.narration,
            tran_type=transaction.tran_type,
            category=transaction.category,
            pay_type=transaction.pay_type,
        )
        
        cust_acct = Account.get(owner_id=transaction.reference)

        if transaction.tran_type == 'payment':
            entry.debit = CommissionAccount.get(code='escrow').account.id
            entry.credit = cust_acct.id
        elif transaction.tran_type == 'bill':
            entry.debit = cust_acct.id        
            entry.credit = Account.get(owner_id=transaction.entity_id).id
        else:
            raise Exception("Failed to determine transaction accounts")

        valid, reason, status = entry.is_valid()
        if valid:
            return entry
        else:
            raise Exception(reason, status)

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

        if self.tran_type == 'payment':
            payment_entry = Entry(
                reference=self.reference,
                amount=self.amount,
                description=self.description,
                tran_type=self.tran_type,
                phone=self.phone,
                pay_type=self.pay_type,
                entity_id=self.entity_id
            )
            payment_entry.debit = Account.get(owner_id=self.entity_id).id
            payment_entry.credit = Account.get(owner_id=self.pay_type).id
            entries.append(payment_entry)

        return entries

    def transact(self):
        """
        :rtype: object
        If a customer is invoiced, value is debited off their account onto
        the entity account, when they make a payment
        1. Value is debited off the `escrow` onto the customer account
        2. Value is also moved off the entity account onto the pay type account

        In the future, the payment type account ought to be created per entity
        """
        valid, reason, status = self.is_valid()
        if not valid:
            raise Exception(reason.get('msg'), status)

        entries = self.get_entries()

        for entr in entries:
            db.session.add(entr)

        db.session.commit()

        
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
    reference = db.Column(db.String(50))  # customer/vendor id
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
