from requests import post
from aws_requests_auth.aws_auth import AWSRequestsAuth
from os import environ
import json
import datetime

'''

# Author: MBastian

This script will iterate through a list of json docs (objects_to_relay) and then index
each document into your Elasticsearch cluster.

- The index name will be dynamically generated. In this case, a new index name will be created each day.

If you're using Amazon's Elasticsearch service, set is_amazon_es = true. This will
enable AWS request signing :)

'''

# ------------------------------ [ Function Declarations ] --------------------------------------#

def post_log_to_es(dumped_json, es_host, index_name, doc_type):
    # Example parameters:
    #
    # index_name = 'applogs-2016-12-08'
    # doc_type = 'std-app-log'
    # es_host = IP/DNS name of Elasticsearch host
    try:
        post_response = post(
                            'http://{}/{}/{}'.format(es_host, index_name, doc_type),
                            data=dumped_json
                        )
        return post_response
    except Exception as ex:
        print("Failed to post data to Elasticsearch! Exception: {}".format(ex), 3)
        return None

# This method will sign the request before sending it off to AWS Elasticsearch
def signed_post_log_to_es(dumped_json, es_host, index_name, doc_type):
    # Example parameters:
    #
    # index_name = 'applogs-2016-12-08'
    # doc_type = 'std-app-log'
    # es_host = self-explanatory
    try:
        # Acquire authorization headers. This is necessary to authenticate with ES via Lambda
        auth = AWSRequestsAuth(aws_access_key=environ['AWS_ACCESS_KEY_ID'],
                               aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'],
                               aws_token=environ['AWS_SESSION_TOKEN'],
                               aws_host=es_host,
                               aws_region='us-east-1',
                               aws_service='es')

        post_response = post(
                            'https://{}/{}/{}'.format(es_host, index_name, doc_type),
                            data=dumped_json,
                            auth=auth
                        )
        return post_response
    except Exception as ex:
        print("Failed to post data to Elasticsearch! Exception: {}".format(ex), 3)
        return None

def identify_index_name():
    # Create an index name that follows this example:
    global index_name_prefix
    return index_name_prefix + datetime.today().date().strftime('%Y.%m.%d')

def identify_es_document_type():
    # TODO: Later, this should take a look at the app name to determine doc type. For now, std-app-log is ok.
    return "std-app-log"

def convert_unix_stamp_to_iso(ux_timestamp):
    try:
        if ux_timestamp is None:
            return None
        else:
            # the TS is in milliseconds, so divide it down.
            return datetime.utcfromtimestamp(ux_timestamp / 1000).isoformat()
    except Exception as e:
        return datetime.now().isoformat()

def log(msg='', level=1):
    global count_errors
    global DebugMode
    switch = {
        1: "Info",
        2: "Warning",
        3: "Error",
        4: "Debug"
    }

    # Don't write out a log message if we aren't in debug mode
    if level == 4 and DebugMode == False:
        return

    print('[{}] :: {}'.format(switch.get(level, "Unknown").upper(), msg))

    if level == 3:
        count_errors = count_errors + 1
        return

def ship_list_to_es(list_docs, es_host, is_amazon_es):
    global count_errors

    for obj_to_post in list_docs:

        json_str_obj = json.dumps(obj_to_post)

        # If this is running locally on a dev machine, don't call method
        # that tries to generate authorization headers.
        if is_amazon_es == False:
            response = post_log_to_es(
                dumped_json=json_str_obj,
                es_host=es_host,
                index_name=identify_index_name(),
                doc_type=identify_es_document_type()
            )
        else:
            # Sign the request using access/secret. Required when
            # you're sending documents to Amazon ES via CURL/Requests
            response = signed_post_log_to_es(
                dumped_json=json_str_obj,
                es_host=es_host,
                index_name=identify_index_name(),
                doc_type=identify_es_document_type()
            )

        log('ES cluster response: {}'.format(response.content), 1)

        if response is not None and response.ok:
            log("Successfully posted log message to ES. HTTP Status code: {}".format(response.status_code))
        elif response is not None and response.status_code != 201:
            log(
                "Failed to post data to Elasticsearch! Response: {} - {}".format(response.status_code,
                                                                                 response.content),
                3
            )
        else:
            log(
                "Failed to post data to Elasticsearch. No exception was thrown, however.", 3
            )

        continue


# ------------------------------ [ Execution Begins ] --------------------------------------#

is_amazon_es = True
DebugMode = True

# This is what your Elasticsearch document's index name should be prefixed with.
# The suffix will be today's date (utc) in this format: YYYY.MM.DD
index_name_prefix = "applogs-"
count_errors = 0

if is_amazon_es is True:
    es_host = "my-elasticsearch-cluster.us-east-1.es.amazonaws.com"
else:
    es_host = "my-elasticsearch.com"

# List of generated log objects to ship to Elasticsearch. Fill this with
# the JSON documents you want to send to ES
objects_to_relay = []

# Pass the list to this function which will iterate the collection and ship
# the messages off
ship_list_to_es(objects_to_relay, es_host, is_amazon_es)

# Check our error count. Raise an exception if necessary.
if count_errors > 0:
    raise Exception("One or more errors occurred whilst relaying logs from CloudWatch into ES.")

