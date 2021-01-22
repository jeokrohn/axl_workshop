import mxnumplan
import urllib3
import ucmaxl

UCM_PUBLISHER = '198.18.133.3'
AXL_USER = 'administrator'
AXL_PASSWORD = 'dCloud123!'

# from connection_parameters import *

def main():
    """
    Mexico in August 2019 will change their national numbering plan to a closed fixed length (10 digit) numbering
    plan:  https://www.itu.int/dms_pub/itu-t/oth/02/02/T020200008A0003PDFE.pdf

    While previously cellphone numbers were easily identifiable by their common prefix in the new numbering plan
    cellphone  numbers share the same prefix(es) as the other geographical numbers. Enterprise admins still want to be
    able  to determine which number are cellphone numbers to be able to implement differentiated class of service (with
    or  without access to cellphone numbers).

    One way to achieve that is to provision blocking translation patterns in UCM to block access to mobile cellphone
    number  ranges. The question remains: What are the cellphone number ranges?

    To answer that question the Mexcian numbering plan authority publishes a CSV file with all number ranges in Mexico
    at:  https://sns.ift.org.mx:8081/sns-frontend/planes-numeracion/descarga-publica.xhtml. This list is continuously
    updated.

    Why not try to build a Pythin script that:

    * pulls the latest numbering plan from the website
    * identifies the mobile ranges
    * summarizes these ranges to a minimal set of patterns
    * provisions blocking translation patterns all of these patterns
    The file mxnumplan.py is such a script which when executed directly takes a number of arguments from the CLI and then
    executes above operations accordingly.

    Instead of invoking the script from the CLI (feel free to try that if you have Python installed) we can also invoke
    code from the script directly.
    """
    # disable warnings for HTTPS sessions w/ diabled cert validation
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    patterns = mxnumplan.patterns_from_web()
    patterns = mxnumplan.optimize_patterns(patterns)

    print(f'summarized to {len(patterns)} patterns')

    # print the 1st few patterns
    print('\n'.join(f'{p.for_ucm}' for p in patterns[:10]))

    # in the interest of execution time we will only consider the 1st 100 patterns for the actual provisioning
    patterns = patterns[:100]

    mxnumplan.provision_patterns(ucm=UCM_PUBLISHER, user=AXL_USER, password=AXL_PASSWORD,
                       read_only=False, route_list_name=None, patterns=patterns)

    return

def delete_patterns():
    mxnumplan.provision_patterns(ucm=UCM_PUBLISHER, user=AXL_USER, password=AXL_PASSWORD,
                                 read_only=False, route_list_name=None, patterns=[])


if __name__ == '__main__':


    main()
    delete_patterns()