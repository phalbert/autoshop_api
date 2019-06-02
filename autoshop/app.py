from flask import Flask

from autoshop import auth, api
from autoshop.extensions import db, jwt, migrate


def create_app(testing=False, cli=False):
    """Application factory, used to create application
    """
    app = Flask('autoshop')
    app.config.from_object('autoshop.config')

    if testing is True:
        app.config['TESTING'] = True

    configure_extensions(app, cli)
    register_blueprints(app)

    return app


def configure_extensions(app, cli):
    """configure flask extensions
    """
    db.init_app(app)
    jwt.init_app(app)

    if cli is True:
        migrate.init_app(app, db)


def register_blueprints(app):
    """register all blueprints for application
    """
    app.register_blueprint(auth.views.blueprint)
    app.register_blueprint(api.views.blueprint)
