### Overview
This is the official repository for [team MIV's](https://malwareintel.io/meet-the-team/) malware tracker.
The tracker can be found [here](http://37.139.17.66:5000/login) and is currently under heavy development.
It is being used to assist with the collection of malware samples from OSINT sources and MIV's
own honeypot networks. It is the intention for the tracker to become a centralised
repository helping MIV members with malware analysis and information dissemination through
the group's [website](https://malwareintel.io/).

The tracker is heavily based on the OSTIP
platform, originally developed by [kx499](https://github.com/kx499).

### Installation

As prep work on Debian or Ubuntu systems, you will need to run ```sudo apt install git python-virtualenv python-pip python-dev```

To install miv-tracker do the following:
- ```git clone https://github.com/team-miv/miv-tracker.git```
- ```virtualenv ostip```
- ```cd ostip```
- ```bin/pip install -r requirements.txt```
- ```scripts/install-redis.sh```
- ```./db_create.py```

To miv-tracker do the following:
- ```../redis-stable/src/redis-server``` *Note: this is started in install-redis.sh, but in subsequent runs, it's required.*
- ```bin/celery -A tasks.celery worker --loglevel=info --beat```
- ```./add_user -u username -p password```
- ```./run.py```

*Note: if not running on localhost, add host=0.0.0.0 to app.run() in run.py, or use* ```./run.py --prod```

### Versioning
This project adheres to [Semantic Versioning](http://semver.org/).
