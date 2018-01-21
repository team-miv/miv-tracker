#!bin/python
from app import app, login_manager
from app.models import Users

from flask_blogging import SQLAStorage, BloggingEngine
from sqlalchemy import create_engine, MetaData

engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = login_manager
meta.create_all(bind=engine)

@blog_engine.user_loader
def load_user(user_id):
    return Users.query.filter(Users.id == int(user_id)).first()

if __name__ == '__main__':
    app.run(debug=True)
