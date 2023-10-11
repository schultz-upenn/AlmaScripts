#!/usr/bin/env python

# *** for set query ***
import lxml.etree as ET
from requests import Session
    
# *** don't keep your API key right in the script ***    
api_key = "yourkey"

# ***  base url for the jobs API ***
base_url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf'

# *** job ID from last screen before Submit ***
job='M12889770000231'
jobs_api = base_url + '/jobs/{job_id}?op=run'

# *** set ID from Manage sets ***
set='12345'
getsetmember_api = base_url + '/sets/{setid}/members?'

# *** Setup requests session *** 
session = Session()
session.headers.update({
    'accept': 'application/xml',
    'authorization': 'apikey {}'.format(api_key),
    'Content-Type':'application/xml'
})

# *** get the set to see if it has any results today ***
set_get = session.get(getsetmember_api.format(setid=set))
setdoc = set_get.text
setdoc = bytes(bytearray(setdoc, encoding='utf-8'))
setroot = ET.fromstring(setdoc)
cnt=setroot.attrib['total_record_count']

# *** here I send email to the metadata experts with a count of records in the set ***


# *** if num records in set isn't zero, run the job on the set ***
if (cnt != '0'):

    values = \
"""<job>
 	<parameters>
 		<parameter>
 			<name>task_MmsTaggingParams_boolean</name>
 			<value>BIBS</value>
 		</parameter>
 		<parameter>
 			<name>set_id</name>
 			<value>12345</value>
 		</parameter>
 		<parameter>
 			<name>job_name</name>
 			<value>Synchronize Bib records with external catalog</value>
 		</parameter>
 	</parameters>
 </job>"""

    # *** kick off the job ***
    kickoff = session.post(jobs_api.format(job_id=job), data=values)

    print(kickoff.text)

