# sec-forms-word-cloud-script
Create a word cloud visualization for SEC filing forms

## About The Project
Listening to the podcast "Robinhood Snacks" inspired me to create this script that scrapes the recent SEC filings and take a look at the frequent words that appear in an automated and fun way.  

![example](documentation/example.png "Example")

The repository that builds and deploys a static website on [GitHub Pages](https://tapaskapadia.github.io/sec-word-clouds/) that utilizes this script can be found [here](https://github.com/tapaskapadia/sec-word-clouds)

Why:
* Jack and Nick, hosts of "Robinhood Snacks", mention using "ctr + f" on S-1 documents for fun insights and focuses for companies
* I enjoy a good word cloud 

What:
* Scrapes [SEC current events](https://www.sec.gov/edgar/searchedgar/currentevents.htm)
* Creates a JSON file with the filing information including all the cleaned words for defined form types (10-K,S-1,ect.)
* Creates a word cloud image for the company based of the data including matching the SIC code with related image masks
* Creates a markdown file to be utilized in for a HUGO website to display the output on [GitHub Pages](https://tapaskapadia.github.io/sec-word-clouds/)

Where:
* Checkout the associated GitHub Project Page utilizing this repository to build and deploy a static website: https://tapaskapadia.github.io/sec-word-clouds/ 

### Built With
Python3 

Main Libraries Include:
* Beautiful Soup
* Jinja2 

## Getting Started
This is an example of how one may get started or utilize this script.
### Prerequisites
Python3 and pip3 are required & utilized to install the dependencies. 
### Installation
1. Clone the repo
2. Install pip packages
```sh
  #python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```
3. Configure environment variables
* DAILY_LIMIT - limit of number of filings to successfully process (There are 100+ S-1 + 10-K forms Daily)
* WORD_CLOUD_OUTPUT_PATH - (default "./generatedImages/") - where to output the generated word clout image
* OUT_FILING_PATH - (default "./filingData/") - where to output the cleaned company filing data
* OUT_MARKDOWN_PATH  - (default "./markdown/") - where to output the generated markdown template
* MARKDOWN_FILE - (default "postMarkdown.j2") - which template file to utilize when generating the markdown files

## Usage
The main.py can be modified as desired. 
Example: 
```sh
  python main.py
  ```
## Roadmap
I will fix bugs that appear.  
Potential TO-DO feature:
* Scraping company logos and using them as masks
* Better error handling
* More image masks for the SIC codes utilized in word cloud generation 
* Storing cleaned filing data in a database
