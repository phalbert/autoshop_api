from autoshop.extensions import db
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

    entity = db.relationship("Entity")
    type = db.relationship("EmployeeType")
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

    employee_id = db.Column(
        db.String(50), db.ForeignKey("employee.uuid"), nullable=False
    )
    request_id = db.Column(
        db.String(50), db.ForeignKey("service_request.uuid"), nullable=False
    )
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime)
    completed_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    employee = db.relationship("Employee")
    request = db.relationship("ServiceRequest")
    entity = db.relationship("Entity")

    def __init__(self, **kwargs):
        super(Job, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<Job %s>" % self.employee_id
 
    @property
    def time(self):
        if self.completed_date:
            import datetime
            from dateutil.relativedelta import relativedelta

            start = self.date_created
            ends = self.completed_date

            diff = relativedelta(ends, start)
            return {
                "years" : diff.years, 
                "months" : diff.months, 
                "days" : diff.days, 
                "hours" : diff.hours, 
                "minutes" : diff.minutes,
                "word": "%d year %d month %d days %d hours %d minutes" % (diff.years, diff.months, diff.days, diff.hours, diff.minutes)
            }
        else:
            return None

    def complete(self):
        from autoshop.models.part import Part,  PartLog
        from autoshop.commons.util import random_tran_id

        job = Job.get(uuid=self.uuid)

        hours = job.time['hours']
        days_in_hours = job.time['days'] * 24
        
        time = hours + days_in_hours


        part = Part.get(code='labour')
        log = PartLog(
            part_id=part.uuid,
            debit=part.uuid,
            credit=part.entity_id,
            reference=random_tran_id(),
            category='sale',
            quantity=time,
            unit_cost=part.price,
            amount=time * int(part.price),          
            entity_id=part.entity_id
        )

        item = JobItem(
            job_id=self.uuid,
            item=part.uuid,
            quantity=time,
            unit_cost=part.price,
            entity_id=part.entity_id
        )

        db.session.add(item)
        db.session.add(log)
        db.session.commit()

class JobItem(db.Model, BaseMixin, AuditableMixin):
    job_id = db.Column(db.String(50), db.ForeignKey("job.uuid"))
    item = db.Column(db.String(50), db.ForeignKey("part.uuid"))
    quantity = db.Column(db.String(50))
    unit_cost = db.Column(db.String(50))
    units = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    part = db.relationship("Part")
    job = db.relationship("Job")
    entity = db.relationship("Entity")

    def __init__(self, **kwargs):
        super(JobItem, self).__init__(**kwargs)
        self.get_uuid()

    def __repr__(self):
        return "<JobItem %s>" % self.uuid
   
    @property
    def cost(self):
        try:
            return int(self.quantity) * int(self.unit_cost)
        except Exception:
            return None

