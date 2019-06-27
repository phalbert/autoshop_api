from flask_jwt_extended import get_jwt_identity

from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin

class PartCategory(db.Model, BaseMixin, AuditableMixin):
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    parent_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(PartCategory, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<PartCategory %s>" % self.name
 
    @property
    def parent(self):
        if self.parent_id and self.parent_id != '0':
            return PartCategory.get(uuid=self.parent_id).name
        else:
            return None

class Part(db.Model, BaseMixin, AuditableMixin):
    """Inventory model
    """
    code = db.Column(db.String(200), nullable=False) # part number
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    category_id = db.Column(db.String(50), db.ForeignKey('part_category.uuid'))
    model_id = db.Column(db.String(50))
    price = db.Column(db.String(50))
    quantity = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    vendor_id = db.Column(db.String(50), db.ForeignKey('vendor.uuid'))
    vendor_price = db.Column(db.String(50))
    
    entity = db.relationship('Entity')
    vendor = db.relationship('Vendor')
    category = db.relationship('PartCategory')

    def __init__(self, **kwargs):
        super(Part, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Part %s>" % self.name

    def increase(self, value=1):
        self.quantity = self.quantity + value
        return self.save()    

    def descrease(self, value=1):
        self.quantity = self.quantity + value
        return self.save()  


class PartLog(db.Model, BaseMixin, AuditableMixin):
    """Inventory log model to track usage
    """

    part_id = db.Column(db.String(50), db.ForeignKey('part.uuid'))
    job_id = db.Column(db.String(50))
    quantity = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    
    entity = db.relationship('Entity')
    part = db.relationship('Part')

    def __init__(self, **kwargs):
        super(PartLog, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<PartLog %s>" % self.name

