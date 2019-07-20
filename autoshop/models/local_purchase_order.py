
from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity


class LocalPurchaseOrder(db.Model, BaseMixin, AuditableMixin):
    """Basic LPO model
    """

    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    vendor_id = db.Column(db.String(50), db.ForeignKey("vendor.uuid"), nullable=False)
    
    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')

    def __init__(self, **kwargs):
        super(LocalPurchaseOrder, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<LocalPurchaseOrder %s>" % self.uuid

class LpoItem(db.Model, BaseMixin, AuditableMixin):
    order_id = db.Column(db.String(50), db.ForeignKey('local_purchase_order.uuid'))
    part_id = db.Column(db.String(80), db.ForeignKey("part.uuid"), nullable=False)
    quantity = db.Column(db.String(50))  
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    
    part = db.relationship('Part')
    order = db.relationship('LocalPurchaseOrder')
    entity = db.relationship('Entity')

    def __init__(self, **kwargs):
        super(LpoItem, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<LpoItem %s>" % self.uuid
