import requests
import argparse
import sys
import getpass
import xmltodict

# This is here ONLY to suppress self-signed certoficate warnings
import urllib3

def operatorInfo(session, server, opname):
    url = f"https://{server}/api/operator/{opname}"
    response = session.get(url, verify=False)

    if response.status_code < 200 or response.status_code >= 300:
        print(f"REST API authentication failed with status {response.status_code}")
        print(f"Reason: {response.text}")
        return None

    xmltree = xmltodict.parse(response.text)

    return xmltree


## Do an operator PUT
def operatorPut(session, server, opname, xmldata):
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

    if response.status_code < 200 or response.status_code >= 300:
        print(f"REST API authentication failed with status {response.status_code}")
        print(f"Reason: {response.text}")
        return False

    return True


def enableOperator(session, server, opname, isMO):
    ## Template for BigFix REST API Operator actions
    if isMO:
        operatorTemplate = f'''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Unrestricted</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()
    else:
        operatorTemplate = '''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>RoleRestricted</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()

    return operatorPut(session, server, opname, operatorTemplate)


def disableOperator(session, server, opname, isMO):
    ## Template for BigFix REST API Operator actions
    if isMO:
        operatorTemplate = '''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Disabled</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()
    else:
        operatorTemplate = '''\
        <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
        <Operator>
        <Name>{opname}</Name>
        <LoginPermission>Disabled</LoginPermission>
        </Operator>
        </BESAPI>
        '''.strip()

    return operatorPut(session, server, opname, operatorTemplate)

def chgOperatorPassword(session, server, opname, password):
    ## Template for BigFix REST API Operator actions
    operatorTemplate = f'''\
    <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Operator>
    <Name>{opname}</Name>
    <Password>{password}</Password>
    </Operator>
    </BESAPI>
    '''.strip()

    return operatorPut(session, server, opname, operatorTemplate)



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

if args.bfpass == None:
    ## TODO: Modify to prompt until 2 consecutive matching passwords
    passwd = getpass.getpass(prompt="Enter REST API password:")
else:
    passwd = args.bfpass


## We have parsed our command line arguments.



## Create HTTP(S) session
session = requests.Session()
session.auth = (args.bfuser, passwd)

response = session.get(f"https://{args.bfserver}/api/login", verify=False)

## Terminate if not a success code
if response.status_code < 200 or response.status_code >= 300:
    print(f"REST API authentication failed with status {response.status_code}")
    print(f"Reason: {response.text}")
    sys.exit(1)

opInfo = operatorInfo(session, args.bfserver, args.operator)

if opInfo == None:
    print("Operator does not exist")
    sys.exit(1)

isMO = False

if opInfo["BESAPI"]["Operator"]["MasterOperator"] == "true":
    isMO = True

if args.enable:
    if not enableOperator(session, args.bfserver, args.operator, isMO):
        sys.exit(1)
elif args.disable:
    if not disableOperator(session, args.bfserver, args.operator, isMO):
        sys.exit(1)
elif args.changepw:
    if not chgOperatorPassword(session, args.bfserver, args.operator, args.changepw):
        sys.exit(1)
else:
    print("Invalid operation")
    sys.exit(1)

print("REST API Operation successful\n")
sys.exit(0)
