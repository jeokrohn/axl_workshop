import zeep
import zeep.cache
import zeep.plugins
import zeep.exceptions
import requests
import os
import logging
from lxml import etree
import urllib3
import itertools

UCM_PUBLISHER = '198.18.133.3'
AXL_USER = 'administrator'
AXL_PASSWORD = 'dCloud123!'

# from connection_parameters import *

# a simple zeep plugin to log all SOAP request and responses to stdin
# a zeep plugin basically has two methods ingress and egress which get called just before sending (egress)
# and just after receiving (ingress) a SOAP request/response
class LoggingPlugin(zeep.plugins.Plugin):
    @staticmethod
    def print_envelope(header, envelope):
        s = etree.tostring(envelope, pretty_print=True).decode().strip()
        print('\n'.join(f'{header}:{l}' for l in s.splitlines()))

    def ingress(self, envelope, http_headers, operation):
        LoggingPlugin.print_envelope('in', envelope)
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        LoggingPlugin.print_envelope('out', envelope)
        return envelope, http_headers


def print_history():
    print('SOAP Request sent to UCM:')
    print(etree.tostring(history.last_sent['envelope'], pretty_print=True).decode())
    print('\nSOAP Response received from UCM:')
    print(etree.tostring(history.last_received['envelope'], pretty_print=True).decode())


def list_phones():
    rt = 'name description product model class protocol'
    rt = {k: '' for k in rt.split()}
    cc = 'userHoldMohAudioSourceId phoneTemplateName mlppDomainId mlppIndicationStatus softkeyTemplateName deviceName'
    rt['currentConfig'] = {k: '' for k in cc.split()}
    dps = service.listPhone(searchCriteria={'name': '%'}, returnedTags=rt, first=5)
    print(dps)


def list_css():
    # Both the searchCriteria and the returnedTags parameter can simply be passed as Python directories with the
    # corresponding key/value mappings.
    tags = ['description', 'clause', 'dialPlanWizardGenId', 'partitionUsage', 'name']
    search_criteria = {'name': '%'}
    r = service.listCss(searchCriteria=search_criteria, returnedTags={t: '' for t in tags}, first=5)

    css_list = r['return'].css
    print(css_list)
    print(type(css_list[0]))

    # All CSS names
    # Attributes of the returned objects can be accessed as attributes because zeep creates class instances based on
    # the class definitions in the WSDL file (see <class 'zeep.objects.LCss'> output before)
    print('\n\n'.join(f'{css.name}({css.uuid}): {css.clause}' for css in css_list))

    # thanks to the history plugin we still have access to the actual request/reponse sent/received
    print('SOAP Request sent to UCM:')
    print(etree.tostring(history.last_sent['envelope'], pretty_print=True).decode())

    print('\nSOAP Response received from UCM:')
    print(etree.tostring(history.last_received['envelope'], pretty_print=True).decode())


def list_process_node():
    r_tags = 'name description mac nodeUsage processNodeRole'
    r = service.listProcessNode(searchCriteria={'name': 'EnterpriseWideData'}, returnedTags={t: '' for t in
                                                                                             r_tags.split()})
    r = r['return'].processNode
    print(r)
    print('\n'.join(' '.join(f'{k}={v:<22}' for k, v in p.__values__.items() if v is not None) for p in r))


def user_str(user):
    """
    create string representation for LUser object
    :param user: LUser
    :return: string representation
    """
    return ', '.join(f'{k}={v}' for k, v in user.__values__.items() if v is not None)


def add_user():
    """
    Try to create a user
    """
    global history

    # list the 1st 10 users
    r = service.listUser(searchCriteria={'lastName': '%'}, returnedTags={'userid': ''}, first=10)
    user_list = r['return'].user
    print(user_list)
    print('\n'.join(user_str(u) for u in user_list))

    # get details of 1st user
    user = user_list[0]
    rt = 'firstName lastName userid presenceGroupName'
    returned_tags = {t: '' for t in rt.split()}
    returned_tags['associatedGroups'] = {'userGroup': {'name': '', 'userRoles': ''}}
    r = service.getUser(uuid=user.uuid, returnedTags=returned_tags)
    user_details = r['return'].user
    print(user_str(user_details))

    # determine list of presence groups
    r = service.listPresenceGroup(searchCriteria={'name': '%'}, returnedTags={'name': ''})
    presence_group_list = r['return'].presenceGroup
    print(presence_group_list)

    # create a user object based on the type definition in the WSDL
    factory = client.type_factory('ns0')
    new_user = factory.XUser(
        firstName='Bob',
        lastName='Barnaby',
        userid='bbarnaby',
        presenceGroupName='Standard Presence group',
        # associated groups is a list of userGroup elements. Each userGroup has a name
        associatedGroups={
            'userGroup': [
                {'name': 'Standard CCM End Users'},
                {'name': 'Standard CTI Enabled'}
            ]
        }
    )

    try:
        r = service.addUser(user=new_user)
    except zeep.exceptions.Fault as fault:
        # catch zeep exception. The Fault object has the AXL errors message and the detail element
        # from which we can extract the integer AXL error code
        axl_code = int(fault.detail.find('.//axlcode').text)
        print(f"Failed to insert user: {axl_code}/{fault.message}")
    else:
        print(r)


class Row:
    # Helper class to create an object based on a row returned from an AXL executeSqlQuery
    def __init__(self, row):
        # save a dictionary of key/value pairs
        self._obj = {e.tag: e.text for e in row}

    def __repr__(self):
        """
        String representation for row object
        :return:
        """
        return f'Row({", ".join(f"{k}={v}" for k, v in self._obj.items())})'

    def __getattr__(self, item):
        """
        Satisfy attribute access by accessing saved directory
        :param item:
        :return:
        """
        return self._obj[item]


def sql_test():
    r = service.executeSQLQuery(sql='select * from processnode')

    rows = r['return'].row
    rows = [Row(r) for r in rows]

    # The Row helper class also allows us to access the values in the rows as attributes.
    names = [r.name for r in rows]
    print(names)

    # ... and the __repr__ method implementation gives us a readable representation of the rows
    print(rows)

    r = service.executeSQLQuery(sql='select name,clause from callingsearchspace')
    rows = [Row(r) for r in r['return'].row]

    # Using simple thin AXL request we can easily execute some validations on the configured CSSes
    # For example: Are there any CSSes without partitions assigned to them?
    csses_wo_partitions = [css.name for css in rows if css.clause is None]
    print(f'CSSes w/o partitions: {", ".join(csses_wo_partitions)}')

    # let's try to determine the set of partitions used in CSSes
    clauses = [r.clause for r in rows]

    # only not empty clauses
    clauses = [c for c in clauses if c is not None]

    # get partition names by splitting at ':'
    clauses = [c.split(':') for c in clauses]

    # now chain all partition names, put them in a set to make them unique, and put them into a dictionary
    # so that it's fast to check for existence of a partition
    used_partitions = set(itertools.chain.from_iterable(clauses))

    # Get all partition names
    r = service.executeSQLQuery(sql='select name from routepartition')
    partition_names = [row[0].text for row in r['return'].row]

    # are there any partitions which are not used in any CSS?
    unused_partitions = [p for p in partition_names if p not in used_partitions]
    print(f'Partitions not used in any CSS: {", ".join(unused_partitions)}')
    return


def try_zeep():
    global transport, history, client, service, factory
    # disable warnings for HTTPS sessions w/ diabled cert validation
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    logging.getLogger('zeep').setLevel(logging.INFO)
    logging.getLogger('zeep.transports').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    logging.basicConfig(level=logging.DEBUG)
    axl_url = f'https://{UCM_PUBLISHER}:8443/axl/'

    # we have WSDL files for a number of releases in the WSDL directory
    wsdl_version = '11.0'
    wsdl = os.path.join(os.path.dirname(__file__), 'WSDL', wsdl_version, 'AXLAPI.wsdl')
    print(f'Using WSDL: {wsdl}')

    # we want to use the same requests session for all requests
    # among other things this makes sure that cookies are handled
    # properly: a sessoon cookies set by UCM in the 1st reaponse
    # will automatically be sent with each following request
    # see:
    # https://developer.cisco.com/docs/axl/#!axl-developer-guide/using-jsessionidsso-to-improve-performance
    session = requests.Session()
    session.auth = (AXL_USER, AXL_PASSWORD)
    session.verify = False

    # setting up the zeep client
    # - we enable the history plugin so that after calling an endpoint we have access to the latest request & response
    # - also we enable our logging plugin above which logs requests and responses in real-time
    transport = zeep.Transport(session=session, cache=zeep.cache.SqliteCache())
    history = zeep.plugins.HistoryPlugin()
    client = zeep.Client(wsdl=wsdl,
                         transport=transport,
                         # create a chain of plugins to keep the history of request/response
                         # and log everything to stdout
                         plugins=[history, LoggingPlugin()])
    # the 1st parameter here is the binding defined in the WSDL
    service = client.create_service('{http://www.cisco.com/AXLAPIService/}AXLAPIBinding', axl_url)

    list_phones()

    list_css()

    list_process_node()

    add_user()

    sql_test()


if __name__ == '__main__':
    try_zeep()
