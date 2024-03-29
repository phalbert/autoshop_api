
from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin


class Service(db.Model, BaseMixin, AuditableMixin):
    """Service model
    """

    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(4000))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    entity = db.relationship("Entity")

    def __init__(self, **kwargs):
        super(Service, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Service %s>" % self.name


class ServiceRequest(db.Model, BaseMixin, AuditableMixin):
    """"
    Service Request
    """

    customer_id = db.Column(db.String(50), db.ForeignKey("customer.uuid"))
    service_id = db.Column(db.String(50), db.ForeignKey("service.uuid"))
    vehicle_id = db.Column(db.String(50), db.ForeignKey("vehicle.uuid"))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    customer = db.relationship("Customer")
    service = db.relationship("Service")
    vehicle = db.relationship("Vehicle")
    entity = db.relationship("Entity")
    job = db.relationship("Job")

    def __init__(self, **kwargs):
        super(ServiceRequest, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<ServiceRequest %s>" % self.uuid


class WorkItem(db.Model, BaseMixin, AuditableMixin):
    request_id = db.Column(db.String(50), db.ForeignKey("service_request.uuid"))
    item = db.Column(db.String(50))
    quantity = db.Column(db.String(50))
    unit_cost = db.Column(db.String(50))
    units = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    request = db.relationship("ServiceRequest")
    entity = db.relationship("Entity")

    def __init__(self, **kwargs):
        super(WorkItem, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<WorkItem %s>" % self.uuid

    @property
    def cost(self):
        try:
            return int(self.quantity) * int(self.unit_cost)
        except Exception:
            return None
