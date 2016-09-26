'''
Author:         MBastian
Date:           9/21/2016
Purpose:        This script will handle the triggering of a Jenkins job within your jenkins server remotely (via https),
                provided that you have Cross-Site Request Forgery (CSRF) protection enabled (as you should).

                When CSRF is enabled, you must provide a "crumb" as a header within your POST request
                that should trigger the jenkins job. Otherwise, you will receive an error stating that
                the crumb is invalid.
'''

import json
import requests

# Name of Jenkins job to trigger via HTTPS POST
jenkins_job_name = 'Put_Jenkins_Job_Name_Here'

# Jenkins job token. Located under the job itself within Jenkins
jenkins_job_token = "myjobtoken_here"

# Base of Jenkins URL
jenkins_base_url = 'https://jenkins.mydomain.com'

# User to be used for authentication against Jenkins crumb api end point.
# Make sure this user has the most restrictive permissions possible
jnk_usr = 'user_for_deploy'
jnk_token = 'token for above user'


def build_remote_jenkins_url():
    # Concatenate the required fields to formulate the Jenkins URL used to trigger
    # the Jenkins job of interest.
    complete_trigger_url = '{}/job/{}/buildWithParameters?token={}'.format(
        jenkins_base_url,
        jenkins_job_name,
        jenkins_job_token
    )
    return complete_trigger_url


def fetch_crumb_from_jenkins(base_jenkins_fqdn, jnk_usr, jnk_token):
    # Purpose: create and return crumb header required to trigger remote jenkins build.

    # get crumb token via Jenkins endpoint listed below. This is done in order to
    # comply with a security mechanism that prevents cross-site request forgery.
    crumb_issue_url = "{}/crumbIssuer/api/json".format(base_jenkins_fqdn)
    try:
        crumb_response = requests.get(crumb_issue_url, auth=(jnk_usr, jnk_token))
        crumb_dict = crumb_response.json()
        print("Crumb response: {}".format(crumb_dict))

        # Extract the crumb field name and crumb value from response
        crumb_field = crumb_dict["crumbRequestField"]
        crumb_value = crumb_dict["crumb"]
        print(
            (
                "Field ID: {}{}".format(crumb_field, "\n") +
                "Crumb: {}".format(crumb_value)
            )
        )
    except Exception as e:
        print("Failed to retrieve crumb. Cannot make API call to Jenkins in lieu of this. Exception: {}".format(e))
        return None

    # Adding crumb as header to api request
    headers = {
        "{}".format(crumb_field): "{}".format(crumb_value)
    }

    print("Successfully retrieved CSRF crumb/field identifier.")

    return headers


def post_to_jenkins_build_url(header_for_crumb, jenkins_trigger_url, jnk_username, jnk_secret):
    # Performs actual POST request to your Jenkins server

    print("Posting to the following url. Note: token is ommitted: {}".format(jenkins_trigger_url.split("?token=")[0]))

    try:
        build_post_resp = requests.post(
            url=jenkins_trigger_url,
            headers=header_for_crumb,
            auth=(jnk_username, jnk_secret)
        )
        print(build_post_resp)
        return build_post_resp
    except e:
        print("FAILED to post to Jenkins build url due to an exception: {}".format(e))
        return None


def trigger_remote_jenkins_build():
    # Fetch crumb from Jenkins server
    crumb_header = fetch_crumb_from_jenkins(
        base_jenkins_fqdn=jenkins_base_url,
        jnk_usr=jnk_usr,
        jnk_token=jnk_token
    )
    if crumb_header is None:
        return

    # Concatenate the respective Jenkins information variables declared above so that
    # we have a valid job url
    complete_trigger_url = build_remote_jenkins_url()

    # Now, pass crumb and uploaded file to primary function that makes POST to Jenkins
    job_POST_results = post_to_jenkins_build_url(
        header_for_crumb=crumb_header,
        jenkins_trigger_url=complete_trigger_url,
        jnk_username=jnk_usr,
        jnk_secret=jnk_token
    )

    # If the response is none, an error was reported inside the method.
    if job_POST_results is None:
        return
    elif job_POST_results.status_code == 201 or job_POST_results.status_code == 200:
        # success status code. This is good.
        print("Successfully triggered Jenkins job!")
        return
    else:
        print(
            (
                "FAIL - A non-success status code was returned by the Jenkins server! " +
                "Status code: {} \nText Response:{}".format(job_POST_results.status_code, job_POST_results.text)
            )
        )
        return


# Here's where the build execution begins. Errors are handled within each method.
trigger_remote_jenkins_build()
