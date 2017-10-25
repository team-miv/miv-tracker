from app import db
from app import app
from .models import Indicator, Control, Itype, Links, Event
from feeder.logentry import ResultsDict
from whois import whois
from ipwhois import IPWhois
import pprint
import re
import concurrent.futures
import datetime
import itertools
import lxml
import lxml.html
import requests
import urllib.parse


def _load_related_data(data):
    ioc = {}
    items = Indicator.query.filter_by(event_id=data.event_id).all()
    [ioc.update({item.ioc: item.id}) for item in items]

    data_types = {}
    d_items = Itype.query.all()
    [data_types.update({d_item.name: [d_item, d_item.regex]}) for d_item in d_items]

    control = Control.query.filter_by(name=data.control).first()
    if not control:
        raise Exception("Control not found")

    for dt in data.data_types.keys():
        data_type = data_types.get(dt)
        if not data_type:
            raise Exception("Data Type not found")

    return ioc, control, data_types


def _correlate(indicator_list):
    # not yet implemented
    for ind_id, ev_id, val in indicator_list:
        for i in Indicator.query.filter_by(ioc=val).all():
            if i.id != ind_id:
                link = Links(ev_id, ind_id, i.event_id, i.id)
                link2 = Links(i.event_id, i.id, ev_id, ind_id)
                db.session.add(link)
                db.session.add(link2)
    db.session.commit()


def _enrich_data(data_type, data, pend=True):
    results = 'Not implemented yet'
    full = 'Not implemented yet'
    if pend:
        if data_type == 'ipv4':
            obj = IPWhois(data)
            q = obj.lookup_rdap(depth=1)
            net = q.get('network', {})
            results = '%s|%s' % (net.get('name'), net.get('cidr'))
            full = pprint.pformat(q)
        elif data_type == 'domain':
            q = whois(data)
            results = '%s|%s|%s' % (q.get('registrar'), q.get('name'), q.get('emails'))
            full = q.text

    return results, full

def _valid_json(fields, data_dict):
    if all(k in data_dict for k in fields):
        for field in fields:
            if re.search('_id$', field):
                try:
                    int(data_dict[field])
                except Exception:
                    return False
        return True

    return False


def _add_indicators(results, pending=False, enrich_it=False):
    reasons = []
    inserted_indicators = []
    failed_indicators = []
    updated_indicators = []
    if not isinstance(results, ResultsDict):
        app.logger.warn('Bad object passed to _add_indicators')
        reasons.append('Bad object passed to _add_indicators')
        return {'success':len(inserted_indicators), 'failed':len(failed_indicators), 'reason':';'.join(reasons)}

    if not Event.query.get(results.event_id):
        app.logger.warn('Event ID %s doesnt exist' % results.event_id)
        reasons.append('Event ID %s doesnt exist' % results.event_id)
        return {'success':len(inserted_indicators), 'failed':len(failed_indicators), 'reason':';'.join(reasons)}

    ioc_list, cont_obj, all_data_types = _load_related_data(results)
    for data_type in results.data_types.keys():
        type_array = all_data_types.get(data_type)
        if not type_array:
            app.logger.warn("Bulk Indicator: Non-existent data type: %s can't process" % data_type)
            reasons.append('Bad Data Type')
            failed_indicators.append([0, results.event_id, [i for i in results.data_types.get(data_type, {}).keys()]])
            continue
        regex = type_array[1]
        if regex:
            regex = re.compile(type_array[1])
        type_obj = type_array[0]
        indicators = results.data_types.get(data_type)
        for i in indicators.keys():
            val = i
            dt = indicators[i]['date']
            desc = indicators[i]['description']
            ind_id = ioc_list.get(val)
            if ind_id:
                ind = Indicator.query.get(ind_id)
                ind.last_seen = dt
                updated_indicators.append([ind_id, results.event_id, val])
            else:
                if (regex and regex.match(val)) or regex is None:
                    enrich, enrich_full = _enrich_data(data_type, val, pending|enrich_it)
                    ind = Indicator(results.event_id, val, desc, cont_obj, type_obj, pending, enrich, enrich_full)
                    db.session.add(ind)
                    db.session.flush()
                    ind_id = ind.id
                    inserted_indicators.append([ind_id, results.event_id, val])
                else:
                    reasons.append('Validation Failed')
                    failed_indicators.append([0, results.event_id, val])

    # commit and correlate
    try:
        db.session.commit()
        if not pending:
            _correlate(inserted_indicators)
    except Exception, e:
        db.session.rollback()
        app.logger.warn('Error committing indicators: %s' % e)
        reasons.append('Commit Failed')
        failed_indicators += inserted_indicators
        inserted_indicators = []

    return {'success':len(inserted_indicators) + len(updated_indicators), 'failed':len(failed_indicators), 'reason':';'.join(reasons)}


def filter_query(query, conditions):
    model_class = query._entities[0].mapper._identity_class # returns the query's Model
    join_class = query._join_entities[0].mapper._identity_class
    for cond in conditions:
        key = cond.get('field')
        op = cond.get('operator')
        value = cond.get('val')

        column = getattr(model_class, key, None) or getattr(join_class, key, None)
        if not column:
            raise Exception('Invalid filter column: %s' % key)
        if op == 'in':
            filt = column.in_(value.split(','))
        else:
            try:
                attr = filter(lambda e: hasattr(column, e % op), ['%s', '%s_', '__%s__'])[0] % op
            except IndexError:
                raise Exception('Invalid filter operator: %s' % op)
        if value == 'null':
            value = None
        filt = getattr(column, attr)(value)
        print filt
        query = query.filter(filt)
        return query

def fix_url(url):
    """Fixes anomalous URL paths
    :param url: the url to fix
    """
    return "http://" + url if "://" not in url else url

def scrape(page, rows_xpath, mapping, next_xpath=None, stop_condition=None):
    """Function to scrape data from web pages
    :param page: the page to scrape
    :param rows_xpath: the xpath to the target data that needs scraping
    :param mapping: parameter to supply a dictionary containing the mapping of
                    scraped data to keywords
    :param next_xpath: the xpath to the target page's "next page" button
    :param stop_condition: parameter to supply a boolean stop condition
    """
    try:
        while page:
            document = lxml.html.fromstring(requests.get(page).text)

            for row in document.xpath(rows_xpath):
                item = {key: value(row) for key, value in mapping.items()}

                yield item

                if stop_condition and stop_condition(row, item):
                    return

            if next_xpath:
                next_links = document.xpath(next_xpath)
                page = urllib.parse.urljoin(page, next_links[
                    0]) if next_links else None

            else:
                page = None

    except requests.ConnectionError:
        # catch connection errors
        # logger.warning('CONNECTION ERROR: scraping [{}]'.format(str(page)))
        pass

    except requests.HTTPError:
        # catch htp errors
        # logger.warning('HTTP ERROR: scraping [{}]'.format(str(page)))
        pass

    except Exception:
        # catch any other exception for debugging purposes
        # logger.critical("EXCEPTION RAISED: scraping [{}]".format(str(page)))
        pass


def scrape_trackers():
    """Function to scrape data from malware trackers"""
    return list(itertools.chain(*concurrent.futures.ThreadPoolExecutor(5).map(
        lambda args: scrape(*args),
        [(
            'http://vxvault.net/ViriList.php',
            "//div[@id='page']/table/tr[td]",
            {
                "date": lambda row: datetime.datetime.strptime(
                    str(datetime.datetime.now().year) + "-" + row[0][0].text,
                    "%Y-%m-%d"),
                "url": lambda row: fix_url(row[1][1].text.strip()),
                "md5": lambda row: row[2][0].text.strip(),
                "ip": lambda row: row[3][0].text.strip(),
            },
            "//a[text()='Next >']/@href",
            lambda row, item: (datetime.datetime.now() - item["date"]).days > 30
        )])))