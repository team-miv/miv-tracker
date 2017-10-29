#!bin/python
from app import db
from app.models import User
import argparse

parser = argparse.ArgumentParser(prog='./add_user')
parser.add_argument("-u", "--username", help="username to add to the database")
parser.add_argument("-p", "--password", help="password to add to the database")
args = parser.parse_args()

# create temporary user account
try:
    admin_user = User(args.username, args.password)
    db.session.add(admin_user)
    db.session.commit()
    print "SUCCESS: added user - {}".format(args.username)
except Exception as e:
    print "ERROR: cannot add user - {}\nSTACKTRACE:\n {}".format(args.username, e)
