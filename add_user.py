#!bin/python
from app import db
from app.models import Users
import argparse

parser = argparse.ArgumentParser(prog='./add_user')
parser.add_argument("-u", "--username", help="username to add to the database")
parser.add_argument("-p", "--password", help="password to add to the database")
parser.add_argument("-r", "--role", choices=('admin', 'user'),
                    help="specify user role")
args = parser.parse_args()

# create user account
try:
    if args.role == 'admin':
        user = Users(args.username, args.password, args.role)
    else:
        user = Users(args.username, args.password, args.role)
    db.session.add(user)
    db.session.commit()
    print "SUCCESS: added user - {}".format(args.username)
except Exception as e:
    print "ERROR: cannot add user - {}\nSTACKTRACE:\n {}".format(args.username, e)
