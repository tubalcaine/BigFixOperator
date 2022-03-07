from typing_extensions import Required
import requests
import argparse
import sys



# This is here ONLY to suppress self-signed certoficate warnings
import urllib3
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
    , required=True
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


## We have parsed our command line arguments.

## Template for BigFix REST API Operator actions
operatorTemplate = f''' \
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
<Operator>
<Name>IEMAdmin</Name>
<!-- THIS is where you can specify a new password -->
<Password>MyNewPassword</Password>
<MasterOperator>true</MasterOperator>
<CustomContent>true</CustomContent>
<ShowOtherActions>true</ShowOtherActions>
<StopOtherActions>true</StopOtherActions>
<CanCreateActions>true</CanCreateActions>
<PostActionBehaviorPrivilege>AllowRestartAndShutdown</PostActionBehaviorPrivilege>
<ActionScriptCommandsPrivilege>AllowRestartAndShutdown</ActionScriptCommandsPrivilege>
<CanLock>true</CanLock>
<CanSendMultipleRefresh>true</CanSendMultipleRefresh>
<CanSubmitQueries>true</CanSubmitQueries>
<LoginPermission>Unrestricted</LoginPermission>
<UnmanagedAssetPrivilege>ShowAll</UnmanagedAssetPrivilege>
<InterfaceLogins
<!-- THESE enable/disable access -->
<Console>true</Console>
<WebUI>true</WebUI>
<API>true</API>
<Applications>
<Name>autopatch</Name>
<Name>cmep</Name>
<Name>content</Name>
<Name>custom</Name>
<Name>insights</Name>
<Name>mdm</Name>
<Name>patch</Name>
<Name>prfmgr</Name>
<Name>query</Name>
<Name>swd</Name>
<Name>workflow</Name>
</Applications>
</InterfaceLogins>
<ComputerAssignments/>
</Operator>
</BESAPI>
'''.strip()

session = requests.Session();
session.auth = (bf_username, bf_password)
response = session.get("https://" + bf_server + "/api/login", verify=False);

qheader = {
	'Content-Type' : 'application/x-www-form-urlencoded'
}

qquery = {
	"relevance" : query,
	"output"    : "json"
}

req = requests.Request('POST'
	, "https://" + bf_server + "/api/query"
	, headers=qheader
	, data=qquery
)

prepped = session.prepare_request(req)

result = session.send(prepped, verify = False)
