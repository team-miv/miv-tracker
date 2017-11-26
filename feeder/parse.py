#!/usr/bin/env python
from app import app, db, utils
import csv
import json
from logentry import ResultsDict
from app.models import Event, Level, Likelihood, Source, Tlp
import re
from sqlalchemy.exc import IntegrityError


class ParseCsv:
    # Example config will look like this
    # Note indicator_<type> is ioc field, date is date and optional, desc_<int> are desc columns and optional
    # fieldnames, data_types, control are required fields
    # "config": {
    #     "fieldnames": ["date", "indicator_ipv4", "desc_1", "desc_2"],
    #     "data_types": ["ipv4"]
    #     "control": "inbound"
    #     "delimiter": ",",
    #     "doublequote": T|F,
    #     "escapechar": "",
    #     "quotechar": "",
    #     "skipinitialspace": T|F
    # }
    # data is a generator or a list of lines

    def __init__(self, config, event, data):

        self.fieldnames = config.get('fieldnames')
        self.data_types = config.get('data_types')
        self.control = config.get('control')
        self.event = event
        self.data = data
        self.dialect = {
            'delimiter': config.get('delimiter', ','),
            'doublequote': config.get('doublequote', True),
            'escapechar': config.get('escapechar', None),
            'quotechar': config.get('quotechar', '"'),
            'skipinitialspace': config.get('skipinitialspace', False)
        }

    def run(self):
        count = 0
        app.logger.info("Processing ParseCsv")
        reader = csv.DictReader(
            self.data,
            fieldnames=self.fieldnames,
            **self.dialect
        )

        results = ResultsDict(self.event, self.control)
        for row in reader:
            for data_type in self.data_types:
                desc_val = []
                ioc = row.get('indicator_%s' % data_type)
                if not ioc:
                    continue
                for i in xrange(1, 10):
                    tmp = row.get('desc_%s' % i)
                    if tmp:
                        desc_val.append(tmp)
                log_date = row.get('date')
                results.new_ind(data_type=data_type,
                                indicator=ioc,
                                date=log_date,
                                description=';'.join(desc_val))
            count += 1
        app.logger.info("ParseCsv processed %s rows", count)
        return results


class ParseText:
    # Example config will look like this
    # Regex will need to have named capture groups the name are as follows:
    #   indicator_<type> is ioc field,
    #   date is date and optional,
    #   desc_<int> are desc columns and optional
    # data_types, control, and regex are required in json config
    # "config": {
    #     "data_types": ["ipv4"]
    #     "control": "inbound"
    #     "regex": "^(?P<date>[^,]+),(?P<indicator_ipv4>[^,]+),(?P<desc>[^,]+)"
    # }
    # data is a generator or a list of lines

    def __init__(self, config, event, data):
        self.data_types = config.get('data_types', [])
        self.control = config.get('control')
        self.regex = config.get('regex')
        self.event = event
        self.data = data

    def run(self):
        count = 0
        app.logger.info("Processing ParseText")
        rex = re.compile(self.regex)
        results = ResultsDict(self.event, self.control)
        for row in self.data:
            m = rex.search(row)
            if not m:
                app.logger.warn("Row did not match regex: %s", row)
                continue
            matches = m.groupdict()
            for data_type in self.data_types:
                desc_val = []
                desc = None
                ioc = matches.get('indicator_%s' % data_type)
                if not ioc:
                    app.logger.warn("no indicator found for: %s", data_type)
                    continue
                for i in xrange(1, 10):
                    tmp = matches.get('desc_%s' % i)
                    if tmp:
                        desc_val.append(tmp)
                log_date = matches.get('date')
                if len(desc_val) > 0:
                    print 'val: %s' % desc_val
                    desc = ';'.join(desc_val)
                results.new_ind(data_type=data_type,
                                indicator=ioc,
                                date=log_date,
                                description=desc)
            count += 1
        app.logger.info("ParseText processed %s lines", count)
        return results


class ParseScrapedData:
    def __init__(self, config, data, source):
        # self.control = config.get('control')
        self.data = data
        self.source = source
        # self.data_types = config.get('data_types', [])
        self.event_json = {"name": "{} scraping".format(self.source),
                           "details": "Observables mined from {}".format(self.source),
                           "confidence": 10, "source": source,
                           "tlp": "Green",
                           "impact": "Low", "likelihood": "Low"}

    def get_source_id(self):
        return Event.query.filter(
            Event.name == '{} scraping'.format(self.source)).first().id

    def add_event(self, payload):
        req_keys = ('name', 'details', 'confidence', 'source', 'tlp', 'impact',
                    'likelihood')

        try:
            pld = payload
        except Exception, e:
            app.logger.info('data error: {}'.format(e))
            return

        if utils._valid_json(req_keys, pld):
            impact = Level.query.filter(Level.name == pld['impact']).first()
            likelihood = Likelihood.query.filter(
                Likelihood.name == pld['likelihood']).first()
            source = Source.query.filter(Source.name == pld['source']).first()
            tlp = Tlp.query.filter(Tlp.name == pld['tlp']).first()
            if not (impact and likelihood and source and tlp):
                app.logger.warning(
                    'impact, likelihood, source, or tlp not found')

            try:
                confidence = int(pld['confidence'])
                if confidence < 0 or confidence > 100:
                    raise Exception
            except Exception, e:
                app.logger.warning(
                    'confidence was not a number between 0 and 100')
                return

            ev = Event(pld['name'], pld['details'], source, tlp, impact,
                       likelihood, confidence)
            db.session.add(ev)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                app.logger.warning('Integrity error - rolled back')
            app.logger.info('success - event_id {}'.format(ev.id))
        else:
            app.logger.warning('error: bad json')

    def add_data(self, data):
        req_keys = ('control', 'data_type', 'event_id', 'pending', 'data')

        try:
            pld = json.loads(data)
        except Exception, e:
            app.logger.warning('error when uploading indicator: {}'.format(e))
            return

        if utils._valid_json(req_keys, pld):
            # load related stuff
            res_dict = ResultsDict(pld['event_id'], pld['control'])
            for val, desc in pld['data']:
                res_dict.new_ind(data_type=pld['data_type'],
                                 indicator=val,
                                 date=None,
                                 description=desc)
            print utils._add_indicators(res_dict, pld['pending'])  # todo: remove
            app.logger.info('success - added indicator from {}'.format(self.source))
        else:
            app.logger.warning('error: bad json')

    def run(self):
        app.logger.info("Processing ParseScrapedData")
        # todo: move this check in init
        if Event.query.filter(Event.name == self.event_json["name"]).first():
            for row in self.data:
                ip_indicator = json.dumps({
                    "event_id": self.get_source_id(),
                    "control": "Inbound",
                    "data_type": "ipv4",
                    "pending": True,
                    "data": [[row['ip'],
                             'malware ip reported by {}'.format(self.source)]]})
                md5_indicator = json.dumps({
                    "event_id": self.get_source_id(),
                    "control": "Inbound",
                    "data_type": "md5",
                    "pending": True,
                    "data": [[row['md5'],
                              'malware md5 reported by {}'.format(self.source)]]})
                url_indicator = json.dumps({
                    "event_id": self.get_source_id(),
                    "control": "Inbound",
                    "data_type": "url",
                    "pending": True,
                    "data": [[row['url'],
                              'malware url reported by {}'.format(self.source)]]})
                self.add_data(ip_indicator)
                self.add_data(md5_indicator)
                self.add_data(url_indicator)
        else:
            # add source
            obj = Source()
            obj.name = self.source
            db.session.add(obj)
            db.session.commit()
            # create event
            self.add_event(self.event_json)
            # todo: add data


if __name__ == '__main__':
    # testing
    from feeder.scrape import get
    parser = ParseScrapedData('', get(), 'vxvault.net')
    parser.run()
