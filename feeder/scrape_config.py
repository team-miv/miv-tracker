import datetime
from scrape import fix_url

vxvault_config = [('http://vxvault.net/ViriList.php',
                   "//div[@id='page']/table/tr[td]",
                   {"date": lambda row: datetime.datetime.strptime(
                    str(datetime.datetime.now().year) + "-" + row[0][0].text,
                    "%Y-%m-%d"),
                    "url": lambda row: fix_url(row[1][1].text.strip()),
                    "md5": lambda row: row[2][0].text.strip(),
                    "ip": lambda row: row[3][0].text.strip(),
                    },
                   "//a[text()='Next >']/@href",
                   lambda row, item: (datetime.datetime.now() - item["date"]).days > 30
                   )]

# zeus_config = [("https://zeustracker.abuse.ch/monitor.php?browse=binaries",
#                 "//table[@class='table' and tr[@class='tabletitle']]/tr[not(@class='tabletitle')]",
#                 {
#                     "date": lambda row: datetime.datetime.strptime(row[0].text, "%Y-%m-%d"),
#                     "url": lambda row: fix_url(row[1][0].text.strip()),
#                     "md5": lambda row: row[3].text.strip(),
#                 }
#                 )]
#
# malwaredomainlist_config = [("http://www.malwaredomainlist.com/mdl.php",
#                              "//table[@class='table' and tr[@class='tabletitle']]/tr[not(@class='tabletitle')]",
#                              {"date": lambda row: datetime.datetime.strptime(row[0][0].text, "%Y/%m/%d_%H:%M"),
#                               "url": lambda row: fix_url(row[1].text.strip()),
#                               "ip": lambda row: row[2].text.strip(),},
#                              "//table[@class='table']/preceding-sibling::center//a[last()-1]/@href",
#                              lambda row, item: (datetime.datetime.now() - item["date"]).days > 30
#                              )]
#
# malcode_config = [("http://malc0de.com/database/",
#                    "//table[@class='prettytable']/tr[td]",
#                    {"date": lambda row: datetime.datetime.strptime(row[0].text, "%Y-%m-%d"),
#                     "url": lambda row: fix_url(row[1].text.strip()),
#                     "md5": lambda row: row[6][0].text.strip(),
#                     "ip": lambda row: row[2][0].text.strip(),
#                     },
#                    "//a[text()='next']/@href"
#                    )]

