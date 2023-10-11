#!/usr/bin/env python

# The API for analytics only returns xml.
# Item API can return json but we're already in xml so xmltodict for both.  

import lxml.etree as ET
from requests import Session
import re
import xmltodict

# *** dotenv reads key-value pairs from a .env file and can set them as environment variables ***
# *** but here I'm using it to return the API key when I send it the name of my API key ***
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# *** Variables ***
api_key = os.environ.get("API_KEY_Katherine")

# *** find urls for APIs here https://developers.exlibrisgroup.com/console/  ***
base_url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1' # na for North America

# *** the correct item_id plus any number for hold and bib will return the correct record *** 
item_api = base_url + '/bibs/{mms_id}/holdings/{holding_id}/items/{item_id}'
getAnalysis_api = base_url + '/analytics/reports?limit=100&{PathOrToken}'

path = "path=%2Fpath%2Fto%2Fthe%2Fanalysis"

# Setup requests session
session = Session()
session.headers.update({
    'accept': 'application/xml',
    'authorization': 'apikey {}'.format(api_key),
    'content-type': 'application/xml'
})

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
 
    # *** get the token and the true/false status of <IsFinished> element ***
    # *** resumption token will not be repeated in later results but you keep using it ***
    if "ResumptionToken" in (set_dict['report']['QueryResult']):
        ResTokn=set_dict['report']['QueryResult']['ResumptionToken']
        path="token=" + ResTokn

    fin=set_dict['report']['QueryResult']['IsFinished']

    # *** loop through every id returned ***
    for val in set_dict['report']['QueryResult']['ResultXml']['rowset']['Row']:
        mms= val['Column1']
        hold= val['Column2']
        item= val['Column3']

        # *** Make an item lookup request and parse as xml ***
        # *** turn into a dictionary. I find it easier to read ***
        # *** not using the barcode lookup because some might not have barcodes ***
        item_get = session.get(item_api.format(mms_id=mms, holding_id=hold, item_id=item))
        itemdoc = item_get.text

        # *** don't continue if there were errors  ***
        if ( not "errorsExist" in itemdoc and not "is not valid" in itemdoc):
            # *** convert to a dictionary ***
            item_dict= {}
            item_dict=xmltodict.parse(itemdoc, encoding="utf-8", dict_constructor=dict)
            # *** now the data is in json-looking format (slide 13) *** 

            # *** ++++++++++++++++++++++++++++++++++++++++++++++++ ***
            # *** Do some stuff with the record *** 
            # *** ++++++++++++++++++++++++++++++++++++++++++++++++ ***

            # *** check 'in temp loc' marker is really off ***
            # *** data in analytics is 24 hours old ***
            templocmarker= str(item_dict['item']['holding_data']['in_temp_location'])

            # *** check there's really something in temp_location ***
            temploc = item_dict['item']['holding_data']['temp_location']

            # *** dont need to update if nothing in temploc field ***
            if (re.match('false', templocmarker) and temploc):
                # *** delete the entire element from what I send back ***
                # *** it wipes out the value in Alma which is what I want ***
                item_dict['item']['holding_data']['temp_location'] = None
                item_dict['item']['holding_data']['temp_library'] = None
                item_dict['item']['holding_data']['temp_policy'] = None
                item_dict['item']['holding_data']['temp_call_number_type']= None
                item_dict['item']['holding_data']['due_back_date'] = None
                item_dict['item']['holding_data']['temp_call_number'] = None

            # *** ++++++++++++++++++++++++++++++++++++++++++++++++ ***
            # *** ++ You're done doing stuff to records ++++++++++ ***
            # *** ++++++++++++++++++++++++++++++++++++++++++++++++ ***

                # *** unparse - which means get it back to xml for input to Alma ***
                xm = xmltodict.unparse(item_dict, pretty=True).encode('utf-8')

                # *** send changed record back to Alma ***
                # *** You can send back the xm from above but I like to write out when troubleshooting ***
                with open('/home/mypath/saveupdatedItem.xml', "wb") as outf:
                    outf.write(xm)
                    outf.close()

                result = session.put(item_api.format(mms_id=mms,holding_id=hold,item_id=item), data=xm)
                #print(result.text)



