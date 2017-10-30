from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from celery import Celery

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"

from app.models import Users


@login_manager.user_loader
def load_user(user_id):
    return Users.query.filter(Users.id == int(user_id)).first()


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

from app import views, models


if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    #acces logs
    a_logger = logging.getLogger('werkzeug')
    handler = RotatingFileHandler('tmp/ostip_access.log', 'a', 1 * 1024 * 1024, 10)
    a_logger.addHandler(handler)

    #error/app info logs
    file_handler = RotatingFileHandler('tmp/ostip.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(module)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('OSTIP startup')

def create_celery_app(app):
    app = app
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    Taskbase = celery.Task

    class ContextTask(Taskbase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return Taskbase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
