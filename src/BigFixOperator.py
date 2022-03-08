import argparse
import sys
import getpass
import requests
import xmltodict

# This is here ONLY to suppress self-signed certoficate warnings
import urllib3

__version__ = "0.0.1"

def get_operator_info(session, server, opname):
    url = f"https://{server}/api/operator/{opname}"
    result = session.get(url, verify=False)

    if result.status_code < 200 or result.status_code >= 300:
        print(f"REST API authentication failed with status {result.status_code}")
        print(f"Reason: {result.text}")
        return None

    xmltree = xmltodict.parse(result.text)

    return xmltree


## Do an operator PUT
def put_operator(session, server, opname, xmldata):
    qheader = {
        'Content-Type' : 'application/x-www-form-urlencoded'
    }

    req = requests.Request('PUT'
        , f"https://{server}/api/operator/{opname}"
        , headers=qheader
        , data=xmldata
    )

    prepped = session.prepare_request(req)

    result = session.send(prepped, verify = False)

    if result.status_code < 200 or result.status_code >= 300:
        print(f"REST API authentication failed with status {result.status_code}")
        print(f"Reason: {result.text}")
        return False

    return True


def enable_operator(session, server, opname, is_m_op):
    ## Template for BigFix REST API Operator actions
    if is_m_op:
        op_xml = f'''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Unrestricted</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()
    else:
        op_xml = f'''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>RoleRestricted</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()

    return put_operator(session, server, opname, op_xml)


def disable_operator(session, server, opname, is_m_op):
    ## Template for BigFix REST API Operator actions
    if is_m_op:
        op_xml = f'''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Disabled</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()
    else:
        op_xml = f'''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Disabled</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()

    return put_operator(session, server, opname, op_xml)

def change_operator_password(session, server, opname, password):
    ## Template for BigFix REST API Operator actions
    op_xml = f'''\
    <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Operator>
    <Name>{opname}</Name>
    <Password>{password}</Password>
    </Operator>
    </BESAPI>
    '''.strip()

    return put_operator(session, server, opname, op_xml)



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# End of warning supression

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--bfserver"
	, help="address and port of BigFix server (hostname:port)"
	, nargs='?'
    , required=True
    , type=str
	)
parser.add_argument("-u", "--bfuser"
	, help="BigFix REST API Username"
	, nargs='?'
    , required=True
    , type=str
	)
parser.add_argument("-p", "--bfpass"
	, help="BigFix REST API Password"
    , type=str
	)
parser.add_argument("-o", "--operator"
	, help="Operator to work on"
    , required=True
    , type=str
	)
## Create an exclusive group
opgroup = parser.add_mutually_exclusive_group(required=True)

opgroup.add_argument("-e", "--enable"
	, help="Enable operator"
    , action="store_true"
	)
opgroup.add_argument("-d", "--disable"
	, help="Disable operator"
    , action="store_true"
	)
opgroup.add_argument("-c", "--changepw"
	, help="Change password"
    , type=str
	)

args = parser.parse_args()

if args.bfpass is None:
    ## TODO: Modify to prompt until 2 consecutive matching passwords
    passwd = getpass.getpass(prompt="Enter REST API password:")
else:
    passwd = args.bfpass

## We have parsed our command line arguments.

## Create HTTP(S) session
g_session = requests.Session()
g_session.auth = (args.bfuser, passwd)

response = g_session.get(f"https://{args.bfserver}/api/login", verify=False)

## Terminate if not a success code
if response.status_code < 200 or response.status_code >= 300:
    print(f"REST API authentication failed with status {response.status_code}")
    print(f"Reason: {response.text}")
    sys.exit(1)

opInfo = get_operator_info(g_session, args.bfserver, args.operator)

if opInfo is None:
    print("Operator does not exist")
    sys.exit(1)

if ("LDAPDN" in opInfo["BESAPI"]["Operator"]) and (args.changepw is not None):
    print("You cannot change the password of an LDAP/AD BigFix user through the REST API")
    sys.exit(1)

g_ismop = False

if opInfo["BESAPI"]["Operator"]["MasterOperator"] == "true":
    g_ismop = True
else:
    lp = opInfo["BESAPI"]["Operator"]["LoginPermission"]
    print(f"This operator's login permission is {lp}")
    if lp == "Unrestricted":
        print("IF YOU USE THIS SCRIPT TO ENABLE THIS USER, the login permission")
        print("will change to RoleRestricted!")

if args.enable:
    if not enable_operator(g_session, args.bfserver, args.operator, g_ismop):
        sys.exit(1)
elif args.disable:
    if not disable_operator(g_session, args.bfserver, args.operator, g_ismop):
        sys.exit(1)
elif args.changepw:
    if not change_operator_password(g_session, args.bfserver, args.operator, args.changepw):
        sys.exit(1)
else:
    print("Invalid operation")
    sys.exit(1)

print("REST API Operation successful\n")
sys.exit(0)
