from flask import Flask, escape, request, make_response
import boto3
from botocore.exceptions import ClientError
import os
import logging
import urllib
import json

app = Flask(__name__)
client = boto3.client('s3')
bucket = os.environ['AWS_S3_BUCKET']
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_file(path):
    logger.error("Getting {}".format(path))
    try:
        result = client.get_object(Bucket=bucket, Key=path)
        body = result['Body'].read()
        return body
    except ClientError as e:
        logger.error(e)
        return None

def machine_exists(project, machine):
    setup = get_file("projects/{}/{}/startup.sh".format(project, machine))
    if setup is None:
        return False
    else:
        return True

@app.errorhandler(404)
def page_not_found(error=None):
    return "Not Found", 404

@app.route('/launch.sh')
def launch_script():
    script = get_file("launch.sh")
    if script is None:
        return page_not_found()

    resp = make_response(script, 200)
    resp.headers['Content-Type'] = 'text/x-shellscript'
    return resp

@app.route('/<project>/<uuid:machine>/setup.sh')
def get_project_setup_script(project, machine):
    if not machine_exists(project, machine):
        return page_not_found()

    script_path = "projects/{}/setup.sh".format(project)
    project_setup = get_file(script_path)
    if project_setup is None:
        project_setup = ""

    script_path = "projects/{}/{}/setup.sh".format(project, machine)
    host_setup = get_file(script_path)
    if host_setup is None:
        host_setup = ""

    content = project_setup + b"\n" + host_setup

    resp = make_response(content, 200)
    resp.headers['Content-Type'] = 'text/x-shellscript'
    return resp

@app.route('/<project>/<uuid:machine>/startup.sh')
def get_startup_script(project, machine):
    if not machine_exists(project, machine):
        return page_not_found()

    script_path = "projects/{}/{}/startup.sh".format(project, machine)
    content = get_file(script_path)
    if content is None:
        return page_not_found()
    resp = make_response(content, 200)
    resp.headers['Content-Type'] = 'text/x-shellscript'
    return resp

@app.route('/<project>/<uuid:machine>/url/resource/<resource>')
def get_resource_url(project, machine, resource):
    if not machine_exists(project, machine):
        return page_not_found()
    
    resource_path = "projects/{}/resources/{}".format(project, resource)
    try:
        url = client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': resource_path}, ExpiresIn=300)
    except ClientError as e:
        logger.error(e)
        return make_response("Internal Error", 500)

    resp = make_response(url, 200)
    resp.headers['Content-Type'] = 'text/plain'
    return resp

@app.route('/<project>/<uuid:machine>/url/output/<resource>')
def get_output_url(project, machine, resource):
    if not machine_exists(project, machine):
        return page_not_found()
    
    resource_path = "projects/{}/{}/outputs/{}".format(project, machine, resource)
    try:
        url = client.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': resource_path}, HttpMethod='PUT', ExpiresIn=600)
    except ClientError as e:
        logger.error(e)
        return make_response("Internal Error", 500)

    resp = make_response(url, 200)
    resp.headers['Content-Type'] = 'text/plain'
    return resp

@app.route('/<project>/<uuid:machine>/resource/<resource>')
def redirect_resource_url(project, machine, resource):
    if not machine_exists(project, machine):
        return page_not_found()
    
    resource_path = "projects/{}/resources/{}".format(project, resource)
    try:
        url = client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': resource_path}, ExpiresIn=300)
    except ClientError as e:
        logger.error(e)
        return make_response("Internal Error", 500)

    resp = make_response("", 302)
    resp.headers['Location'] = url
    return resp

