#!bin/python
from app import app
from datetime import datetime
from feeder.parse import ParseScrapedData
from feeder.scrape_config import vxvault_config
from feeder.scrape import scrape_source
import schedule
import time


def jobs():
    """Runs parsing jobs"""
    parser = ParseScrapedData(scrape_source(vxvault_config), 'vxvault.net')
    parser.run()


schedule.every().day.at("19:55").do(jobs)

app.logger.info('scheduler started on {}'.format(datetime.now()))
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        app.logger.info('scheduler stopped on {}'.format(datetime.now()))
        exit()
