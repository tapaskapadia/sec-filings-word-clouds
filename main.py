import helpers
import requests
from urllib.parse import urljoin

import time
from os import getenv
START_TIME = time.perf_counter()
# Number of visualizations to create on a daily run
# There seems to be ~100 daily between the form types which seem excessive
DAILY_LIMIT = int(getenv("DAILY_LIMIT","1"))

#makes call to the url provided, and returns soup with lxml parser
secIndexSoup = helpers.getDailySoup()

# grab only the links to the supported document types index pages and transform them into the corresponding .txt page
# shuffles the list 
dailyForms = helpers.parseDailyForms(secIndexSoup)

formListIndex, processedForms = 0, []
# stop when processed the daily limit or stop there are not more forms to analyze
while len(processedForms) <  DAILY_LIMIT and formListIndex < len(dailyForms):
    try:
        time.sleep(.5)
        formUrl = dailyForms[formListIndex]
        formListIndex += 1
        filingData = helpers.analyzeForm(formUrl, processedForms)
        helpers.createWordCloud(filingData)
        helpers.saveFilingData(filingData)
        helpers.generateTemplate(filingData)
        processedForms.append((filingData["companyName"], filingData["formType"]))
    except Exception as e:
        print(f"Something did not go quite right with {formUrl}: {e}")
        continue
END_TIME = time.perf_counter()
print(f"Processed {len(processedForms)} forms in {END_TIME - START_TIME:0.4f} seconds")
