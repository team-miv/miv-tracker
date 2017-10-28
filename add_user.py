from app import db
from app.models import User

# create temporary user account
user_email = ''
passwd = ''
try:
    admin_user = User(user_email, passwd)
    db.session.add(admin_user)
    db.session.commit()
    print "SUCCESS: added user - {}".format(user_email)
except Exception as e:
    print "ERROR: cannot add user - {}\nSTACKTRACE:\n {}".format(user_email, e)
