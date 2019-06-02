from autoshop.commons.dbaccess import query
from autoshop.extensions import db, pwd_context
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin, PersonMixin


class User(db.Model, BaseMixin, AuditableMixin, PersonMixin):
    """Basic user model
    """

    __tablename__ = "users"

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80))
    password = db.Column(db.String(255), nullable=False)
    role_code = db.Column(db.String(50))
    company_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = pwd_context.hash(self.password)
        self.get_uuid()

    def __repr__(self):
        return "<User %s>" % self.username

    @property
    def role(self):
        """Get the role."""
        role = Role.query.filter_by(uuid=self.role_code).first()
        if role is None:
            return None
        return role.name

    @property
    def category(self):
        """Get the role category."""
        role = Role.query.filter_by(uuid=self.role_code).first()
        if role is None:
            return None
        return role.category

    @property
    def company(self):
        try:
            if self.company_id == "system":
                return "System"
            else:
                sql = (
                    """ name
                FROM account_holders
                where uuid = '"""
                    + self.company_id
                    + """'
                """
                )
                data = query(sql)
                return data[0]["name"]
        except Exception:
            return ""


class Role(db.Model, BaseMixin, AuditableMixin):
    name = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(50))
    notes = db.Column(db.String(255))

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Role %s>" % self.name
