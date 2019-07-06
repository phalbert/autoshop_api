from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity


class Customer(db.Model, BaseMixin, AuditableMixin):
    """Basic Customer model
    """

    name = db.Column(db.String(80))
    phone = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50))
    address = db.Column(db.String(500))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    type_id = db.Column(
        db.String(50), db.ForeignKey("customer_type.uuid"), nullable=False
    )
    vehicles = db.relationship("Vehicle", back_populates="customer")

    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Customer %s>" % self.uuid

    @property
    def entity(self):
        entity = Entity.get(uuid=self.entity_id)
        if entity is None:
            return None
        return entity.name

    @property
    def account(self):
        return Account.get(owner_id=self.uuid)
