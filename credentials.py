# MIT License
# ===========
#
# MIT No Attribution
# 
# Copyright <YEAR> <COPYRIGHT HOLDER>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#


import boto3


sts_client = boto3.client('sts', region_name='us-west-2')
ec2_client = boto3.client('ec2', region_name='us-west-2')

response_1 = sts_client.get_caller_identity()

RoleArn = "arn:aws:iam::{}:role/MGN_Agent_Installation_Role".format(response_1['Account'])
RoleSessionName = "well-architected-migration"
response_2 = sts_client.assume_role(
    RoleArn=RoleArn,
    RoleSessionName=RoleSessionName
)

access_key_id = response_2['Credentials']['AccessKeyId']
secret_key = response_2['Credentials']['SecretAccessKey']
session_token = response_2['Credentials']['SessionToken']
response_3 = ec2_client.describe_vpc_endpoints()
vpc_endpoints = response_3['VpcEndpoints']
for vpce in vpc_endpoints:
	if vpce['VpcEndpointType'] == 'Interface' and vpce['ServiceName'] == 'com.amazonaws.us-west-2.s3':
		s3_dns_name = vpce['DnsEntries'][0]['DnsName'][2:]
	elif vpce['VpcEndpointType'] == 'Interface' and vpce['ServiceName'] == 'com.amazonaws.us-west-2.mgn':
		mgn_dns_name = vpce['DnsEntries'][0]['DnsName']

f = open("C:\\Users\\Administrator\\Desktop\\agent_commands.txt", "w+")
f.write("---=== Linux commands: ===--- ")
f.write("\n")
f.write("1 - Download AWS MGN agent installer:")
f.write("\n")
f.write("wget -O ./aws-replication-installer-init.py https://aws-application-migration-service-us-west-2.s3.amazonaws.com/latest/linux/aws-replication-installer-init.py")
f.write("\n")
f.write("2 - Use this command to run the installer:")
f.write("\n")
f.write("sudo python3 aws-replication-installer-init.py --no-prompt --region us-west-2 --aws-access-key-id {} --aws-secret-access-key {} --aws-session-token {} --endpoint {} --s3-endpoint {}".format(access_key_id,secret_key,session_token,mgn_dns_name,s3_dns_name))
f.write("\n")
f.write("\n")
f.write("\n")
f.write("---=== Windows commands: ===--- ")
f.write("\n")
f.write("1 - Download AWS MGN agent installer (use PowerShell):")
f.write("\n")
f.write("wget -O ./AwsReplicationWindowsInstaller.exe https://aws-application-migration-service-us-west-2.s3.us-west-2.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe")
f.write("\n")
f.write("2 - Use this command to run the installer:")
f.write("\n")
f.write("./AWSReplicationWindowsInstaller.exe --no-prompt --region us-west-2 --aws-access-key-id {} --aws-secret-access-key {} --aws-session-token {} --endpoint {} --s3-endpoint {}".format(access_key_id,secret_key,session_token,mgn_dns_name,s3_dns_name))
f.write("\n")
f.close()