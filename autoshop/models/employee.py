
from autoshop.extensions import db
from autoshop.models.account import Account
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity

class EmployeeType(db.Model, BaseMixin, AuditableMixin):
    """"
       mechanic, finance, 
    """

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50))
    entity_id = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(EmployeeType, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<EmployeeType %s>" % self.name

class Employee(db.Model, BaseMixin, AuditableMixin):
    """Basic Employee model
    """

    name = db.Column(db.String(80))
    phone = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50))
    address = db.Column(db.String(500))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    type_id = db.Column(
        db.String(50), db.ForeignKey("employee_type.uuid"), nullable=False
    )

    entity = db.relationship('Entity')
    type = db.relationship('EmployeeType')
    jobs = db.relationship("Job", back_populates="employee")

    def __init__(self, **kwargs):
        super(Employee, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Employee %s>" % self.uuid

    @property
    def entity(self):
        entity = Entity.get(uuid=self.entity_id)
        if entity is None:
            return None
        return entity.name


class Job(db.Model, BaseMixin, AuditableMixin):
    """"
       job cards 
    """

    employee_id = db.Column(db.String(50), db.ForeignKey("employee.uuid"), nullable=False)
    request_id = db.Column(db.String(50), db.ForeignKey("service_request.uuid"), nullable=False)
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime)
    completed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
 
    employee = db.relationship('Employee')
    request = db.relationship('ServiceRequest')
    entity = db.relationship('Entity')

    def __init__(self, **kwargs):
        super(Job, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Job %s>" % self.employee_id

class JobItem(db.Model, BaseMixin, AuditableMixin):
    job_id = db.Column(db.String(50), db.ForeignKey('job.uuid'))
    item = db.Column(db.String(50),  db.ForeignKey('part.uuid'))
    quantity = db.Column(db.String(50))
    unit_cost = db.Column(db.String(50))
    units = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey('entity.uuid'))
    
    part = db.relationship('Part')
    job = db.relationship('Job')
    entity = db.relationship('Entity')

    def __init__(self, **kwargs):
        super(JobItem, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<JobItem %s>" % self.uuid

    @property
    def cost(self):
        try:
            return int(self.quantity) * int(self.unit_cost)
        except Exception as e:
            return None
    
    @property
    def part(self):
        try:
            return int(self.quantity) * int(self.unit_cost)
        except Exception as e:
            return None
