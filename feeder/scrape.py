from app import app
import concurrent.futures
import datetime
import itertools
import lxml
import lxml.html
import requests
from urlparse import urljoin


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
                page = urljoin(page, next_links[
                    0]) if next_links else None

            else:
                page = None

    except requests.ConnectionError:
        # catch connection errors
        app.logger.warning('connection error: scraping [{}]'.format(str(page)))

    except requests.HTTPError:
        # catch htp errors
        app.logger.warning('http error: scraping [{}]'.format(str(page)))

    except Exception:
        # catch any other exception for debugging purposes
        app.logger.critical("error: scraping [{}]".format(str(page)))


def scrape_source(config):
    """Function to scrape data from malware sources"""
    return list(itertools.chain(*concurrent.futures.ThreadPoolExecutor(5).map(
        lambda args: scrape(*args), config)))


if __name__ == '__main__':
    ''''''
