import boto3

# Create S3 Buckets for ELB access logs in all regions
# This script will:
#  - retrieve a list of all AWS regions
#  - create an s3 bucket in each region for the purpose of storing ELB logs

ec2client = boto3.client('ec2')
regions = [region['RegionName'] for region in ec2client.describe_regions()['Regions']]

s3 = boto3.client('s3')
bucket_name_prefix = "nm-dev-elb-logs-"

for reg in regions:
  bucket_name = bucket_name_prefix + reg
  print("Creating s3 bucket: {} for elb logs in region: {}".format(bucket_name, reg))
  try:
      s3.create_bucket(Bucket=bucket_name,
                       ACL = 'private'
      )
  except Exception as e:
      print("An exception occurred! {}".format(e))
      break
