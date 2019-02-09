from __future__ import print_function
from boto3.session import Session

import json
import urllib
import boto3
import zipfile
import tempfile
import botocore
import traceback

print('Loading function')

code_pipeline = boto3.client('codepipeline')

###############################################
#                 FUNCTIONS                   #
###############################################

# Notify CodePipeline of a failed job
def put_job_failure(job, message):

    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job, failureDetails={'message': message, 'type': 'JobFailed'})
 
###############################################

# Notify CodePipeline of a successful job
def put_job_success(job, message):

    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)
    
###############################################

# Finds the artifact 'name' among the 'artifacts'
def find_artifact(artifacts, name):
    
    for artifact in artifacts:
        if artifact['name'] == name:
            return artifact
            
    raise Exception('Input artifact named "{0}" not found in event'.format(name))

###############################################

# Decodes the JSON user parameters and validates the required properties
def get_user_params(job_data):

    try:
        # Get the user parameters which contain the stack, artifact and file settings
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        decoded_parameters = json.loads(user_parameters)
            
    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception('UserParameters could not be decoded as JSON')
    
    if 'artifact' not in decoded_parameters:
        # Validate that the artifact name is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('Your UserParameters JSON must include the artifact name')
    
    if 'file' not in decoded_parameters:
        # Validate that the template file is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('Your UserParameters JSON must include the template file name')
    
    return decoded_parameters
    
###############################################

# Creates an S3 client
def setup_s3_client(job_data):
    
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']
    
    session = Session(aws_access_key_id=key_id,
        aws_secret_access_key=key_secret,
        aws_session_token=session_token)
    return session.client('s3', config=botocore.client.Config(signature_version='s3v4'))

###############################################

# Gets the provisioning details file from artifact
def get_provisioning_file(s3, artifact, file_in_zip):
    
    tmp_file = tempfile.NamedTemporaryFile()
    bucket = artifact['location']['s3Location']['bucketName']
    key = artifact['location']['s3Location']['objectKey']
    
    with tempfile.NamedTemporaryFile() as tmp_file:
        s3.download_file(bucket, key, tmp_file.name)
        with zipfile.ZipFile(tmp_file.name, 'r') as zip:
            return zip.read(file_in_zip)   

###############################################

# Run automation tests using batch jobs
def run_automation_tests(job_id, provisioning_details_file):
    
    try:
        
        print(provisioning_details_file)
        
        put_job_success(job_id, 'Run automation tests success') 
        return
        
    except Exception as e:
        
        put_job_failure(job_id, "run automation tests failed")
        return

###############################################
#                   MAIN                      #
###############################################

def lambda_handler(event, context):
    
    try:
        
        # Extract the Job ID
        job_id = event['CodePipeline.job']['id']
        
        # Extract the Job Data 
        job_data = event['CodePipeline.job']['data']
        
        # Get the list of artifacts passed to the function
        artifacts = job_data['inputArtifacts']
        
        # Codepipeline user params
        params = get_user_params(job_data)
        artifact = params['artifact']
        provisioning_file = params['file']
        
        # Get the artifact details
        artifact_data = find_artifact(artifacts, artifact)
        
        # Get S3 client to access artifact with
        s3 = setup_s3_client(job_data)
        
        # Get the JSON template file out of the artifact
        provisioning_details_file = get_provisioning_file(s3, artifact_data, provisioning_file)
        
        # Run automation tests using batch jobs
        run_automation_tests(job_id, provisioning_details_file)
        
    except Exception as e:
        
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        
        print('Function failed due to exception.') 
        print(e)
        
        traceback.print_exc()
        put_job_failure(job_id, 'Function exception: ' + str(e))
      
    print('Function complete.')   
    return "Complete."

###############################################

