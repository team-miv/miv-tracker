from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin
from flask_bcrypt import Bcrypt
from celery import Celery
from flask_blogging import SQLAStorage, BloggingEngine
from sqlalchemy import create_engine, MetaData

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"
from app import views, models

app.config["BLOGGING_SITENAME"] = "MALWAREINTELVAULT"
app.config["BLOGGING_URL_PREFIX"] = "/blog"
app.config["BLOGGING_DISQUS_SITENAME"] = "test"
app.config["BLOGGING_SITEURL"] = "http://localhost:5000/index"
app.config["BLOGGING_SITENAME"] = "MALWAREINTELVAULT"
app.config["BLOGGING_KEYWORDS"] = ["locky", "malware", "new strain"]
app.config["FILEUPLOAD_IMG_FOLDER"] = "fileupload"
app.config["FILEUPLOAD_PREFIX"] = "/fileupload"
app.config["FILEUPLOAD_ALLOWED_EXTENSIONS"] = ["png", "jpg", "jpeg", "gif"]

engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)

from app.models import Users


@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return Users.query.filter(Users.id == int(user_id)).first()


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/')


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
