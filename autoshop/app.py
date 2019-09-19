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
    register_requestloggers(app)

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


def register_requestloggers(app):
    """Register custom request loggers."""
    import datetime
    import time
    from flask import g, request
    from rfc3339 import rfc3339

    @app.before_request
    def start_timer():
        g.start = time.time()

    @app.after_request
    def log_request(response):
        if request.path == "/favicon.ico":
            return response
        elif request.path.startswith("/static"):
            return response

        now = time.time()
        duration = round(now - g.start, 2)
        dt = datetime.datetime.fromtimestamp(now)
        timestamp = rfc3339(dt, utc=True)

        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        host = request.host.split(":", 1)[0]
        args = dict(request.args)

        log_params = [
            ("method", request.method, "blue"),
            ("path", request.path, "blue"),
            ("status", response.status_code, "yellow"),
            ("duration", duration, "green"),
            ("time", timestamp, "magenta"),
            ("ip", ip, "red"),
            ("host", host, "red"),
            ("params", args, "blue"),
        ]

        request_id = request.headers.get("X-Request-ID")
        if request_id:
            log_params.append(("request_id", request_id, "yellow"))

        parts = []
        for name, value, color in log_params:
            part = "{}={}".format(name, value)  # colors.color(, fg=color)
            parts.append(part)
        line = " ".join(parts)

        # from loguru import logger

        app.logger.info(line)
        app.logger.info(request.get_data())
        app.logger.info(response.data)
        return response
