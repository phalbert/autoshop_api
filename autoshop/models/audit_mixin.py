# Inspired by the flask-specific https://gist.github.com/ngse/c20058116b8044c65d3fbceda3fdf423
# This is generic and should work with any web framework and even command-line.

# Implement by using AuditableMixin in your model class declarations

# Usage for the [Reahl web app framework](http://reahl.org) below:
# ---------------------------------------------------------------

# import lib.audit_mixin

# lib.audit_mixin.PLEASE_AUDIT = [lib.audit_mixin.ACTION_UPDATE]

# def current_user_id():
#    current_account = LoginSession.for_current_session().account
#    return current_account.id
# lib.audit_mixin._current_user_id_or_none = current_user_id

# class ImportantThing(lib.audit_mixin.AuditableMixin, Base):
#    blah blah


import datetime
import json

from flask_jwt_extended import get_jwt_identity
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UnicodeText,
    event,
    inspect,
)
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import get_history

from autoshop.extensions import db

ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"

# Only audit the events in this list
PLEASE_AUDIT = [ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE]


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)


def _current_user_id_or_none():
    try:
        identity = get_jwt_identity()
        return identity
    except:
        return None


class MyBase(db.Model):
    """Base model class to implement db columns and features every model should have"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False)


class TimestampableMixin:
    """Allow a model to track its creation and update times"""

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class AuditLog(TimestampableMixin, MyBase):
    """Model an audit log of user actions"""

    user_id = Column(Integer, doc="The ID of the user who made the change")
    target_type = Column(
        String(100), nullable=False, doc="The table name of the altered object"
    )
    target_id = Column(String(50), doc="The ID of the altered object")
    action = Column(String(50), doc="Create (1), update (2), or delete (3)")
    state_before = Column(
        UnicodeText,
        doc="Stores a JSON string representation of a dict containing the altered column "
        "names and original values",
    )
    state_after = Column(
        UnicodeText,
        doc="Stores a JSON string representation of a dict containing the altered column "
        "names and new values",
    )

    def __init__(self, target_type, target_id, action, state_before, state_after):
        self.user_id = _current_user_id_or_none()
        self.target_type = target_type
        self.target_id = target_id
        self.action = action
        self.state_before = state_before
        self.state_after = state_after

    def __repr__(self):
        return "<AuditLog %r: %r -> %r>" % (self.user_id, self.target_type, self.action)

    def save(self, connection):
        connection.execute(
            self.__table__.insert(),
            user_id=self.user_id,
            target_type=self.target_type,
            target_id=self.target_id,
            action=self.action,
            state_before=self.state_before,
            state_after=self.state_after,
        )

    def log(self):
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


class AuditableMixin:
    """Allow a model to be automatically audited"""

    @staticmethod
    def create_audit(connection, object_type, object_id, action, **kwargs):
        audit = AuditLog(
            object_type,
            object_id,
            action,
            kwargs.get("state_before"),
            kwargs.get("state_after"),
        )
        audit.save(connection)

    @classmethod
    def __declare_last__(cls):
        if ACTION_CREATE in PLEASE_AUDIT:
            event.listen(cls, "after_insert", cls.audit_insert)

        if ACTION_DELETE in PLEASE_AUDIT:
            event.listen(cls, "after_delete", cls.audit_delete)

        if ACTION_UPDATE in PLEASE_AUDIT:
            event.listen(cls, "after_update", cls.audit_update)

    @staticmethod
    def audit_insert(mapper, connection, target):
        """Listen for the `after_insert` event and create an AuditLog entry"""
        target.create_audit(connection, target.__tablename__, target.id, ACTION_CREATE)

    @staticmethod
    def audit_delete(mapper, connection, target):
        """Listen for the `after_delete` event and create an AuditLog entry"""
        # target.create_audit(connection, target.__tablename__, target.id, ACTION_DELETE)
        state_before = {}

        attrs = class_mapper(target.__class__).column_attrs
        for attr in attrs:
            state_before[attr.key] = getattr(target, attr.key)

        target.create_audit(
            connection,
            target.__tablename__,
            target.id,
            ACTION_DELETE,
            state_before=json.dumps(state_before, cls=DatetimeEncoder),
            state_after=None,
        )

    @staticmethod
    def audit_update(mapper, connection, target):
        """Listen for the `after_update` event and create an AuditLog entry with before and after state changes"""
        state_before = {}
        state_after = {}
        inspr = inspect(target)
        attrs = class_mapper(target.__class__).column_attrs
        for attr in attrs:
            hist = getattr(inspr.attrs, attr.key).history
            if hist.has_changes():
                state_before[attr.key] = get_history(target, attr.key)[2].pop()
                state_after[attr.key] = getattr(target, attr.key)

        target.create_audit(
            connection,
            target.__tablename__,
            target.id,
            ACTION_UPDATE,
            state_before=json.dumps(state_before, cls=DatetimeEncoder),
            state_after=json.dumps(state_after, cls=DatetimeEncoder),
        )
