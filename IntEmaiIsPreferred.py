#!/usr/bin/env python

# use analytics to return a set of primary ids if the user
# has an internal email address that is marked preferred. compare to incoming data feed and 
# if the user is in it, remove email block. 
 
import lxml.etree as ET
from requests import Session
import re
import xmltodict

# *** dotenv ***
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# *** Variables ***
api_key = os.environ.get("API_KEY_Katherine")

# *** find urls for APIs here https://developers.exlibrisgroup.com/console/  ***
base_url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1' # na for North America
getAnalysis_api = base_url + '/analytics/reports?limit=100&{PathOrToken}'

path = "path=pathtomyreport"

# Setup requests session
session = Session()
session.headers.update({
    'accept': 'application/xml',
    'authorization': 'apikey {}'.format(api_key),
    'content-type': 'application/xml'
})

# *** open file here it's the primary ids  ***
xmlfile=open('/home/pathtomyfile/IntEmailPref_today.xml', 'w')

xmlfile.write('<users>')
xmlfile.write('\n')

# *** get the analysis ***
# *** first time: put in path.  after that: token ***
# *** fin (IsFinished) starts as false ***
fin = 'false'

while fin != 'true':
    set_get = session.get(getAnalysis_api.format(PathOrToken=path))
    set_doc = set_get.text

    # *** convert to a dictionary ***
    # *** input is xml not a lxml tree element ***
    set_dict= {}
    set_dict=xmltodict.parse(set_doc, encoding="utf-8", dict_constructor=dict) 
 
    # *** get the token and the t/f status of 'finished' ***
    # *** if the resumption token element exists *** 
    if "ResumptionToken" in (set_dict['report']['QueryResult']):
        path=set_dict['report']['QueryResult']['ResumptionToken']
        path="token=" + path

    fin=set_dict['report']['QueryResult']['IsFinished']

    # *** loop through every id returned ***
    for val in set_dict['report']['QueryResult']['ResultXml']['rowset']['Row']:
        usr= val['Column1']
        print usr
        xmlfile.write('\t<user>')
        xmlfile.write(usr)
        xmlfile.write('</user>\n')


xmlfile.write('</users>')
xmlfile.write('\n')
xmlfile.close


