"""

Purpose: Identify RDS instances with Multi-AZ deployment enabled

MBastian - 11.11.2016 - initial creation

Pulls a list of RDS instances from AWS and will print
a small report that details instances with multi-az enabled. Ideally, only
production database instances should need multi-az.

The default AWS profile configured on the local machine will be used, by default.


"""

import boto3
from operator import itemgetter

client = boto3.client('rds')

instances = client.describe_db_instances()['DBInstances']
sorted_list = sorted(instances, key=itemgetter('MultiAZ'))

multiAzTrue = [x for x in sorted_list if x['MultiAZ'] is True]
multiAzFalse = [x for x in sorted_list if x['MultiAZ'] is False]

print("-------------------------------------------------")
print("RDS Instances with Multi-AZ deployment enabled:")
print("-------------------------------------------------\n")

for i in multiAzTrue:
    isMultiAz = i['MultiAZ']
    instanceId = i['DBInstanceIdentifier']
    instanceType = i['DBInstanceClass']
    print("Instance: {}\nInstance Type: {}\nMultiAZ: {}\n".format(instanceId, instanceType, isMultiAz))

print("-------------------------------------------------")
print("RDS Instances with Multi-AZ deployment disabled:")
print("-------------------------------------------------")

for i in multiAzFalse:
    isMultiAz = i['MultiAZ']
    instanceId = i['DBInstanceIdentifier']
    instanceType = i['DBInstanceClass']

    print("Instance: {}\nInstance Type: {}\nMultiAZ: {}\n".format(instanceId, instanceType, isMultiAz))




