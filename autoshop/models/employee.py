import datetime
from flask import current_app
from autoshop.extensions import db
from autoshop.models.audit_mixin import AuditableMixin
from autoshop.models.base_mixin import BaseMixin
from autoshop.models.entity import Entity
from autoshop.models.item import ItemLog

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
    completed_date = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
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
        from autoshop.models.item import Item,  ItemLog
        from autoshop.commons.util import random_tran_id

        job = Job.get(uuid=self.uuid)

        hours = job.time['hours']
        days_in_hours = job.time['days'] * 24
        
        time = hours + days_in_hours

        if time == 0 and job.time['minutes'] > 0:
            time = 1


        item = Item.get(code='labour')
        if item:
            log = ItemLog(
                item_id=item.uuid,
                debit=item.uuid,
                credit=item.entity_id,
                reference=random_tran_id(),
                category='sale',
                quantity=time,
                unit_cost=item.price,
                amount=time * int(item.price),          
                entity_id=item.entity_id
            )

            job_item = JobItem(
                job_id=self.uuid,
                item_id=item.uuid,
                quantity=time,
                unit_cost=item.price,
                entity_id=item.entity_id
            )

            db.session.add(job_item)
            db.session.add(log)
            db.session.commit()

class JobItem(db.Model, BaseMixin, AuditableMixin):
    job_id = db.Column(db.String(50), db.ForeignKey("job.uuid"))
    item_id = db.Column(db.String(50), db.ForeignKey("item.uuid"))
    quantity = db.Column(db.String(50))
    unit_cost = db.Column(db.String(50))
    units = db.Column(db.String(50))
    entity_id = db.Column(db.String(50), db.ForeignKey("entity.uuid"))

    item = db.relationship("Item")
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

    def save(self):
        item_log = ItemLog.init_jobitem(self)
        db.session.add(self)
        item_log.transact()
