![alt tag](https://github.com/team-miv/miv-tracker/blob/master/doc/logo.JPG)

### Overview
This is the official repository for [team MIV's](https://malwareintel.io/meet-the-team/) malware tracker.
The tracker can be found [here](http://37.139.17.66:5000/login) and is currently under heavy development.
It is being used to assist with the collection of malware samples from OSINT sources and MIV's
own honeypot network. It is the intention for the tracker to become a centralised
repository helping MIV members with malware analysis and information dissemination through
the group's [website](https://malwareintel.io/).

The tracker is heavily based on the OSTIP
platform, originally developed by [kx499](https://github.com/kx499).

### Installation

As prep work on Debian or Ubuntu systems, you will need to run ```sudo apt install git python-virtualenv python-pip python-dev```

To install miv-tracker do the following:
- ```git clone https://github.com/team-miv/miv-tracker.git```
- ```virtualenv venv```
- ```cd venv```
- ```bin/pip install -r requirements.txt```
- ```./db_create.py``` *Note: on first time installation, you will be asked to supply an administrator username and password*
- ```./db_populate.py```

To run miv-tracker locally for testing and development purposes do the following:
- ```source venv/bin/activate```
- ```./run.py```

For production environments it is advised to serve miv-tracker via gunicorn behing Nginx
acting as a front end reverse proxy. Instructions to do so can be found [here](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04).

### Post-installation configuration options


### Versioning
This project adheres to [Semantic Versioning](http://semver.org/).
