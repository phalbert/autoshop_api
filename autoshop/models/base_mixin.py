import string
import uuid
from random import choice, randint


from autoshop.commons.dbaccess import query
from autoshop.extensions import db


class PersonMixin:
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))


class BaseMixin:
    """Allow a model to track its creation and update times"""

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True)
    active = db.Column(db.Boolean, default=True)
    modified_by = db.Column(db.Integer)
    created_by = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # @declared_attr
    # def user_id(cls):
    #     return db.Column(
    #         db.String(50), db.ForeignKey("users.id"), nullable=False
    #     )

    # @declared_attr
    # def user(cls):
    #     return db.relationship('User')

    @classmethod
    def get(cls, **kwargs):
        """Get a specific object from the database."""
        return cls.query.filter_by(**kwargs).first()

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

    def serialize(self):
        """Convert sqlalchemy object to python dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def get_uuid(self):
        if not self.uuid:
            self.uuid = uuid.uuid4().hex

    def creator(self):
        try:
            sql = (
                """ first_name + ' ' + last_name as username
            FROM users
            where users.id = """
                + str(self.created_by)
                + """
            """
            )
            data = query(sql)
            return data if data is None else data[0]["username"]
        except Exception:
            return ""

    def created_on(self):
        if self.date_created is not None:
            return self.date_created.strftime("%Y-%m-%d %I:%M:%S %p")

    def log(self, label):
        try:
            self.save()
            self.__generate_code__(label)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }

    def update(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                "message": "Ensure the object you're saving is valid.",
                "exception": str(e),
            }

    def __generate_code__(self, label):
        """Generate the resource code."""
        model_id = str(self.id)

        switcher = {1: "000" + model_id, 2: "00" + model_id, 3: "0" + model_id}

        result = switcher.get(len(model_id), model_id)
        result.upper()

        min_char = 2
        max_char = 2
        allchar = string.ascii_letters
        salt = "".join(choice(allchar) for x in range(randint(min_char, max_char)))

        self.uuid = label + salt.upper() + result
        return self
