import helpers
import requests
from urllib.parse import urljoin

import time
from os import getenv
START_TIME = time.perf_counter()


SUPPORTED_FORMS = ["10-K","S-1"]
DAILY_LIMIT = int(getenv("DAILY_LIMIT","10"))
SEC_BASE_URL = "https://www.sec.gov/"
RECENT_FORMS_URL = urljoin(SEC_BASE_URL,"cgi-bin/current?q1=0&q2=6&q3=")

#print(RECENT_FORMS_URL)

#makes call to the url provided, and returns soup with lxml parser
secIndexSoup = helpers.makeCallReturnSoup(RECENT_FORMS_URL)
#print(secIndexSoup)


#grab only the links to the supported document types index pages and transform them into the corresponding .txt page
dailyForms = [urljoin(SEC_BASE_URL, atag['href']).replace("-index.html",".txt") for atag in secIndexSoup.find_all('a',href=True) if "-index.html" in atag['href'] and atag.text in SUPPORTED_FORMS]
helpers.shuffleList(dailyForms)
for f in range(DAILY_LIMIT):
    try:
        filingData = helpers.analyzeForm(dailyForms[f])
        helpers.createWordCloud(filingData)
        helpers.saveFilingData(filingData)
        helpers.generateTemplate(filingData)
    except Exception as e:
        print(f"Something did not go quite right with {dailyForms[f]}: {e}")
        continue
END_TIME = time.perf_counter()
print(f"Processed {DAILY_LIMIT} forms in {END_TIME - START_TIME:0.4f} seconds")
