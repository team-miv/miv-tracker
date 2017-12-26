#!bin/python
import os.path

# check if tmp folder exists
print "[*] checking if tmp folder exists"
if not os.path.exists("tmp"):
    print "[*] missing tmp directory ... creating"
    try:
        os.makedirs("tmp")
    except Exception as e:
        print "[*] creation of tmp directory failed, reason:\n{}".format(e)
else:
    print "[*] tmp folder exists"

from config import APP_NAME
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import Users
from sqlalchemy.exc import IntegrityError

print "[*] creating database"
db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

# check if admin user exists
print "[*] checking if admin user exists"
if not db.session.query(Users).one_or_none():
    print "[*] missing admin user"
    username = raw_input("[*] please input admin user email: ")
    password = raw_input("[*] please input admin user password: ")
    try:
        user = Users(username, password, "admin")
        db.session.add(user)
        db.session.commit()
        print "[*] added user [{}] to database".format(username)
    except IntegrityError as e:
        print "[*] failed adding user [{}] due to error: {}".format(username, e)
else:
    print "[*] admin user exists"

print "[*] {} ready to use".format(APP_NAME)
