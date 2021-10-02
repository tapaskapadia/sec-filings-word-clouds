import requests
import re
import random
import numpy as np
import os
import glob
import random
import json
from math import floor
from PIL import Image
from datetime import datetime 
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Comment
from collections import Counter
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from jinja2 import Environment, FileSystemLoader

SEC_BASE_URL = "https://www.sec.gov/"
# Have Checked these 2 form types but do not see why it would break on others
SUPPORTED_FORMS = ["10-K","S-1"]
# Uninteresting words to filter out 
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "ain", "all", "am", "an", "and", "any", "are", "aren", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "couldn", "couldn't", "d", "did", "didn", "didn't", "do", "does", "doesn", "doesn't", "doing", "don", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn", "hadn't", "has", "hasn", "hasn't", "have", "haven", "haven't", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn", "isn't", "it", "it's", "its", "itself", "just", "ll", "m", "ma", "me", "mightn", "mightn't", "more", "most", "mustn", "mustn't", "my", "myself", "needn", "needn't", "no", "nor", "not", "now", "o", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "re", "s", "same", "shan", "shan't", "she", "she's", "should", "should've", "shouldn", "shouldn't", "so", "some", "such", "t", "than", "that", "that'll", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "ve", "very", "was", "wasn", "wasn't", "we", "were", "weren", "weren't", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "won", "won't", "wouldn", "wouldn't", "y", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "could", "he'd", "he'll", "he's", "here's", "how's", "i'd", "i'll", "i'm", "i've", "let's", "ought", "she'd", "she'll", "that's", "there's", "they'd", "they'll", "they're", "they've", "we'd", "we'll", "we're", "we've", "what's", "when's", "where's", "who's", "why's", "would"]
# The more words in the cloud the longer it takes to generate
MAX_WORDS_IN_CLOUD = int(os.getenv("MAX_WORDS_IN_CLOUD","600"))
# Rule J of the 10-K form allows asset backed security companies to omit many sections
# so there is not good data.
SKIP_ASSET_BACKED_SECURITIES_10K = True
# Skip if the same company and same form type was used in the same day
SKIP_SAME_COMPANY_SAME_FORM = True


OUT_IMG_PATH = os.getenv("WORD_CLOUD_OUTPUT_PATH","./generatedImages/")
OUT_FILING_PATH = os.getenv("OUT_FILING_PATH","./filingData/")
OUT_MARKDOWN_PATH = os.getenv("OUT_MARKDOWN_PATH","./markdown/")
MARKDOWN_FILE = os.getenv("MARKDOWN_FILE","postMarkdown.j2")

def makeCall(url):
    headers = {
    'User-Agent': 'Friendly Software Engineer Visualizing Data for Fun'
    }
    r = requests.get(url, headers=headers)
    return r.content

def makeSoup(content,parserType="lxml"):
    return BeautifulSoup(content, parserType)

def makeCallReturnSoup(url,parserType="lxml"):
    r = makeCall(url)
    return makeSoup(r,parserType=parserType)

# may do a little more structured shuffle in the future
def shuffleList(inputList):
    random.shuffle(inputList)
    return

def filterStopWord(freqDict):
    for sw in STOP_WORDS:
        if sw in freqDict:
            del freqDict[sw]
    return freqDict
# Helps filter out invisible html fields words
def tagVisible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]', 'noscript','xbrli','xbrli:startdate','xbrli:instant','xbrli:measure','xbrldi:explicitmember', 'xbrli:enddate','xbrli:identifier','ix:nonfraction','ix:nonnumeric']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def getDailySoup():
    recentFormsUrl = urljoin(SEC_BASE_URL,"cgi-bin/current?q1=0&q2=6&q3=")
    return makeCallReturnSoup(recentFormsUrl)

def parseDailyForms(soup):
    dailyList = [urljoin(SEC_BASE_URL, atag['href']).replace("-index.html",".txt") for atag in soup.find_all('a',href=True) if "-index.html" in atag['href'] and atag.text in SUPPORTED_FORMS]
    shuffleList(dailyList)
    return dailyList

def parseSecHeader(soup):
    try:
        formObject = {}
        secHeaderText = soup.find('sec-header').text
        formObject["companyName"]  = re.sub(r"[$\\.,@&]","",re.search("COMPANY CONFORMED NAME:(.*)",secHeaderText).group(1).strip())
        formObject["formType"] = re.search("FORM TYPE:(.*)", secHeaderText).group(1).strip()
        companyIndustryRaw = re.search("STANDARD INDUSTRIAL CLASSIFICATION:(.*)(\[.*)", secHeaderText)
        if companyIndustryRaw:
            formObject["companyIndustry"] = companyIndustryRaw.group(1).strip()
            if SKIP_ASSET_BACKED_SECURITIES_10K and formObject["companyIndustry"] == "ASSET-BACKED SECURITIES" and formObject["formType"] == "10-K":
                # ASSET-BACKED SECURITIES omit many sections
                # Defined in section J: https://www.sec.gov/about/forms/form10-k.pdf
                raise Exception("Skipping - Company is in the ASSET-BACKED SECURITIES industry which does not have interesting data")
            formObject["companySicCode"] = companyIndustryRaw.group(2).strip()
        else:
            formObject["companyIndustry"] = "Missing_From_SEC_Filing_Header"
            formObject["companySicCode"] = "[None]"
        formObject["dateFiled"] = re.search("FILED AS OF DATE:(.*)", secHeaderText).group(1).strip()
        return formObject
    except Exception as e:
        raise Exception("Error parsing SEC header: ", e)

def topFreqCount(counterObj, elements=5):
   # should not be calling this function on regular dictionary
    if not isinstance(counterObj,Counter):
        raise Exception("Invalid Counter Object argument: topFreqCount function can only be invoked with a collections.Counter object") 
    # something probably went wrong if this condition is invoked
    if elements > len(counterObj):
        elements = len(counterObj)
    return dict(counterObj.most_common(elements))

def analyzeForm(formUrl, dailyCompanyForms):
    formSoup = makeCallReturnSoup(formUrl)
    print(formSoup)
    formData = parseSecHeader(formSoup)
    # skip times when companies have multiple of the same forms filed on the same day
    # not sure on the why companies file it this way
    if SKIP_SAME_COMPANY_SAME_FORM and tuple([formData['companyName'], formData['formType']]) in dailyCompanyForms:
        raise Exception("Skipping company as same company with the same form type has already been visualized today.")
    
    for filingDocument in formSoup.find_all('document'):
        if filingDocument.type.find(text=True, recursive=False).strip() == formData['formType']:
            pageSoup = BeautifulSoup(str(filingDocument),'html.parser')
            pageText = pageSoup.find_all(text=True)
            visibleTexts = filter(tagVisible, pageText)
            textData = u" ".join(t.strip() for t in visibleTexts)
            c = Counter(re.findall(r"[\w']+", textData.lower()))
            break
    # common filler words are not interesting
    cleanedCounter = filterStopWord(c)
    formData["wordCounts"] = cleanedCounter
    formData["totalWordsCleaned"] = sum(cleanedCounter.values())
    formData["topWords"] = topFreqCount(cleanedCounter)
    formData["formUrl"] = formUrl
    #formatted to be filename friendly
    formData["currentDatetime"] = datetime.now().strftime("%Y%m%d-%H%M%S")
    return formData

def createWordCloudFileName(filingData,outFilingPath=OUT_IMG_PATH):
    return f"{outFilingPath}{filingData['companyName'].replace(' ', '')}_{filingData['formType']}_{filingData['currentDatetime']}.png"

def getMaskImgPath(secCode):
    #Get the major SIC Code group - first 2 numbers
    sicMajorGroup = secCode[1:3]
    majorSecFolder = glob.glob('./secCodesImages/' + sicMajorGroup + '*')
    if len(majorSecFolder) == 1:
        return random.choice(glob.glob(majorSecFolder[0] + '/*')) 
    # pick random file from `Random` folder for image mask
    return random.choice(glob.glob('./secCodesImages/Random/*'))

def createWordCloud(filingData, outImgPath=OUT_IMG_PATH):
    try:
        print("Trying to create word cloud for: ", filingData["companyName"])
        # TO DO: Structure the Mask Images better - picking random file in a folder
        # seems not ideal.
        img = Image.open(getMaskImgPath(filingData["companySicCode"]))
        # RGB Mode required for wordcloud library as gray scale is not implmented correctly
        mask = np.array(img if img.mode == "RGB" else img.convert('RGB'))
        # Generate word cloud
        wordcloud = WordCloud(background_color="white", mode="RGBA", max_words=MAX_WORDS_IN_CLOUD, mask=mask, relative_scaling=.8).generate_from_frequencies(filingData['wordCounts'])
        imageColors = ImageColorGenerator(mask)
        wordcloud.recolor(color_func=imageColors).to_file(createWordCloudFileName(filingData, outFilingPath=outImgPath))
    except Exception as e:
        print("Uh oh - something bad happened when trying to make the wordcloud: ", e)

def createFilingDataFileName(filingData,outFilingPath=OUT_FILING_PATH):
    return f"{outFilingPath}{filingData['companyName'].replace(' ', '')}_{filingData['formType']}_{filingData['currentDatetime']}.json"

def saveFilingData(filingData,outFilingPath=OUT_FILING_PATH):
    try:
        with open(createFilingDataFileName(filingData,outFilingPath), 'w') as f: 
            json.dump(filingData, f) 
    except Exception as e:
        print("Uh oh: - something bad happened when trying to save filingData to disk: ", e)

# used for jinja2 template
def formatStringTime(value, inputformat='%Y%m%d',outputFormat='%m-%d-%Y'):
    datetimeObj = datetime.strptime(value,inputformat)
    return datetimeObj.strftime(outputFormat)

def renderedTemplateName(filingData, outRenderPath=OUT_MARKDOWN_PATH):
    return f"{outRenderPath}{filingData['companyName'].replace(' ', '')}_{filingData['formType']}_{filingData['currentDatetime']}.md"

def saveMarkdownFile(renderedTemplate, filingData, outFilingPath=OUT_MARKDOWN_PATH):
    try:
        with open(renderedTemplateName(filingData,outFilingPath), 'w') as f: 
            f.write(renderedTemplate)
    except Exception as e:
        print("Uh oh: - something bad happened when trying to save rendered template to disk: ", e)

def generateTemplate(filingData, templateFile=MARKDOWN_FILE, outFilingPath=OUT_MARKDOWN_PATH):
    env = Environment(
        loader=FileSystemLoader('./'),
    )
    env.filters['formatStringTime'] = formatStringTime
    markdownTemplate = env.get_template(templateFile)
    renderedTemplate = markdownTemplate.render(filingData, IMAGE_FILE=createWordCloudFileName(filingData,outFilingPath=""), DATA_FILE=createFilingDataFileName(filingData,outFilingPath=""), NUM_UTILIZED_WORDS=MAX_WORDS_IN_CLOUD)
    saveMarkdownFile(renderedTemplate, filingData, outFilingPath=outFilingPath)