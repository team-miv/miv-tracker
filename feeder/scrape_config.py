import datetime
from scrape import fix_url

vxvault_config = [(
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
        )]
