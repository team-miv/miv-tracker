import concurrent.futures
import datetime
import itertools
import lxml
import lxml.html
import requests
import urllib.parse


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

if __name__ == '__main__':
    ''''''
