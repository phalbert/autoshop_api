from autoshop.commons.dbaccess import query
from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.user import User


class AccountType(db.Model, BaseMixin, AuditableMixin):
    """AccountType model
    Types are entity, vendor, customer, suspense, commission
    """

    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(4000), nullable=False)

    def __init__(self, **kwargs):
        super(AccountType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<AccountType %s>" % self.name

    def creator(self):
        """Get the creator."""
        return User.query.filter_by(id=self.created_by).first()


class Account(db.Model, BaseMixin, AuditableMixin):
    """An Account is a store of value for the entity,
    vendor and customer
    """

    __tablename__ = "accounts"

    send_sms = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.String(50), unique=True)
    acc_type = db.Column(db.String(50))
    group = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(Account, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Account %s>" % self.name

    @property
    def balance(self):
        """Get the account balance."""
        try:
            return query(" balance from account_balances where id=" + str(self.id))[0][
                "balance"
            ]
        except Exception:
            return 0

    @property
    def name(self):
        """
        Get the limits per category..
        this is the summation of all entries under a category
        """
        sql = (""" name FROM accounts INNER JOIN account_holders on
        account_holders.uuid=accounts.owner_id where accounts.id =
        """ + str(self.id) + """""")

        data = query(sql)
        return data if data is None else data[0]["name"]

    @property
    def wallets(self):
        """
        Get the limits per category..
        this is the summation of all entries under a category
        """
        sql = (""" accounts.id,account_ledgers.category,category.name,
        COALESCE(sum(account_ledgers.amount), 0.0) as balance FROM accounts
        LEFT OUTER JOIN account_ledgers ON accounts.id = account_ledgers.account_id
        INNER JOIN category on category.uuid=account_ledgers.category where
        accounts.id = """ + str(self.id) + """
        GROUP BY accounts.id,account_ledgers.category,category.name """)

        wallets = query(sql)
        if not wallets:
            return []
        return wallets

    @property
    def no_of_wallets(self):
        """
        Get the limits per category..
        this is the summation of all entries under a category
        """
        sql = (""" accounts.id,account_ledgers.category,category.name,
        COALESCE(sum(account_ledgers.amount), 0.0) as balance FROM accounts
        LEFT OUTER JOIN account_ledgers ON accounts.id = account_ledgers.account_id
        INNER JOIN category on category.uuid=account_ledgers.category
        where accounts.id = """ + str(self.id) + """
        GROUP BY accounts.id,account_ledgers.category,category.name""")

        wallets = query(sql)
        if wallets is None:
            return 0
        return len(wallets)
