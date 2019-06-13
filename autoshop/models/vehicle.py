
from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin


class VehicleModel(db.Model, BaseMixin, AuditableMixin):

    name = db.Column(db.String(50), unique=True, nullable=False)
    fuel_type = db.Column(db.String(50))
    type_id = db.Column(db.String(50), db.ForeignKey('vehicle_type.uuid'))
    transmission = db.Column(db.String(50))
    description = db.Column(db.String(2000))
    type = db.relationship('VehicleType')

    def __init__(self, **kwargs):
        super(VehicleModel, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<VehicleModel %s>" % self.uuid


class VehicleType(db.Model, BaseMixin, AuditableMixin):

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(2000))

    def __init__(self, **kwargs):
        super(VehicleType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<VehicleType %s>" % self.uuid


class Vehicle(db.Model, BaseMixin, AuditableMixin):

    registration_no = db.Column(db.String(50))
    chassis_no = db.Column(db.String(50))
    model_id = db.Column(db.String(50), db.ForeignKey('vehicle_model.uuid'))
    model_no = db.Column(db.String(50))
    engine_no = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(50))
    customer_id = db.Column(db.String(50), db.ForeignKey("customer.uuid"))
    customer = db.relationship("Customer", back_populates="vehicles")
    vehicle_model = db.relationship('VehicleModel')

    def __init__(self, **kwargs):
        super(Vehicle, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Vehicle %s>" % self.uuid

