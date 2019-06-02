from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin

entity_vendors = db.Table(
    "entity_vendors",
    db.Column("entity_id", db.Integer, db.ForeignKey("entity.id"), nullable=False),
    db.Column("vendor_id", db.Integer, db.ForeignKey("vendor.id"), nullable=False),
    db.PrimaryKeyConstraint("entity_id", "vendor_id"),
)


class Entity(db.Model, BaseMixin, AuditableMixin):
    """Entity model
    """

    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    description = db.Column(db.String(4000))
    vendors = db.relationship(
        "Vendor",
        secondary=entity_vendors,
        backref=db.backref("entities", lazy="dynamic"),
        lazy="dynamic",
    )
    customers = db.relationship("Customer", lazy="dynamic")

    def __init__(self, **kwargs):
        super(Entity, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Entity %s>" % self.name

    @property
    def account(self):
        return Account.get(owner_id=self.uuid)

    def add_vendor(self, vendor):
        if not self.is_entity_vendor(vendor):
            self.vendors.append(vendor)

    def remove_vendor(self, vendor):
        if self.is_entity_vendor(vendor):
            self.vendors.remove(vendor)

    def is_entity_vendor(self, vendor):
        return self.vendors.filter(entity_vendors.c.vendor_id == vendor.id).count() > 0


class Vendor(db.Model, BaseMixin, AuditableMixin):
    """Vendor model
    """

    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    description = db.Column(db.String(4000))

    def __init__(self, **kwargs):
        super(Vendor, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Vendor %s>" % self.name

    @property
    def account(self):
        return Account.get(owner_id=self.uuid)


class Group(db.Model, BaseMixin, AuditableMixin):
    """An entity may have groups: these are companies/departments that
    subscribe to their plans on behalf of their staff"""

    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    entity_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Group %s>" % self.name

    @property
    def entity(self):
        entity = Entity.get(uuid=self.entity_id)
        if entity is None:
            return None
        return entity.name
