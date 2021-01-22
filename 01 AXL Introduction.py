import requests
import xmltodict
import json
import urllib3
from lxml import etree, objectify

UCM_PUBLISHER = '198.18.133.3'
AXL_USER = 'administrator'
AXL_PASSWORD = 'dCloud123!'

# from connection_parameters import *

def axl_test():
    # disable warnings for HTTPS sessions w/ diabled cert validation
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    axl_endpoint = f'https://{UCM_PUBLISHER}:8443/axl'

    print(f'Accessing {axl_endpoint}')
    r = requests.get(axl_endpoint, auth=(AXL_USER, AXL_PASSWORD), verify=False)
    r.raise_for_status()
    print(r.text)

def get_version():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    axl_endpoint = f'https://{UCM_PUBLISHER}:8443/axl/'
    body = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/11.0">
            <soapenv:Header/>
            <soapenv:Body>
                <ns:getCCMVersion>
                </ns:getCCMVersion>
            </soapenv:Body>
        </soapenv:Envelope>"""
    headers = {
        'SOAPAction': 'CUCM:DB ver=11.0 getCCMVersion',
        'Content-Type': 'text/xml;charset=UTF-8'
    }
    r = requests.post(axl_endpoint, auth=(AXL_USER, AXL_PASSWORD), verify=False, data=body, headers=headers)
    print(r.text)

    element_tree = etree.fromstring(r.text.encode())
    print(element_tree)

    print(etree.tostring(element_tree, pretty_print=True).decode())

    version:etree._Element = element_tree.find('.//version')
    print(f'Version: {version.text}')

def list_css():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    axl_endpoint = f'https://{UCM_PUBLISHER}:8443/axl/'

    body = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:ns="http://www.cisco.com/AXL/API/11.0">
       <soapenv:Header/>
       <soapenv:Body>
          <ns:listCss >
             <searchCriteria>
                <name>%</name>
             </searchCriteria>
             <returnedTags uuid="?">
                <description>?</description>
                <clause>?</clause>
                <dialPlanWizardGenId>?</dialPlanWizardGenId>
                <partitionUsage>?</partitionUsage>
                <name>?</name>
             </returnedTags>
             <first>10</first>
          </ns:listCss>
       </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        'SOAPAction': 'CUCM:DB ver=11.0 listCss',
        'Content-Type': 'text/xml;charset=UTF-8'
    }
    r = requests.post(axl_endpoint, auth=(AXL_USER, AXL_PASSWORD), verify=False, data=body, headers=headers)
    r.raise_for_status()

    element_tree = etree.fromstring(r.text.encode())
    print(etree.tostring(element_tree, pretty_print=True).decode())

    axl_return = element_tree.find('.//return')
    css_list = []
    for css_element in axl_return:
        css = {e.tag:e.text for e in css_element}
        css_list.append(css)
    print(css_list)

if __name__ == '__main__':
    axl_test()
    get_version()
    list_css()

