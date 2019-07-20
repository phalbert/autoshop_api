from autoshop.models.audit_mixin import AuditableMixin
from autoshop.extensions import db


class AccessLog(db.Model, AuditableMixin):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    ip = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(50))
    region = db.Column(db.String(50))
    country = db.Column(db.String(50))
    location = db.Column(db.String(50))
    isp = db.Column(db.String(50))
    url = db.Column(db.String(50))
    status = db.Column(db.String(4000))
    created_by = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, **kwargs):
        super(AccessLog, self).__init__(**kwargs)

    def __repr__(self):
        return "<AccessLog %s>" % self.ip

    def save(self):
        """Save an object in the database."""
        try:
            # db.session.session.expire_on_commit = False
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }
