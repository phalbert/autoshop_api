
from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity


class LocalPurchaseOrder(db.Model, BaseMixin, AuditableMixin):
    """Basic LPO model
    """

    part_id = db.Column(db.String(80), db.ForeignKey("part.uuid"), nullable=False)
    quantity = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    vendor_id = db.Column(db.String(50), db.ForeignKey("vendor.uuid"), nullable=False)
    
    part = db.relationship('Part')
    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')

    def __init__(self, **kwargs):
        super(LocalPurchaseOrder, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<LocalPurchaseOrder %s>" % self.uuid