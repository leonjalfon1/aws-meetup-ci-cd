from botocore.vendored import requests
import json
import boto3
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

# Clean S3 Bucket (remove all content)
def clean_bucket(job_id, bucket):

    try:
        
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket)
        for obj in bucket.objects.filter():
            s3.Object(bucket.name, obj.key).delete()
        
        put_job_success(job_id, 'Bucket content removed') 
        return
        
    except Exception as e:
        
        put_job_failure(job_id, "Error removing bucket content")
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
        
        # Codepipeline user params
        params = get_user_params(job_data)
        bucket_name = params['bucket']
        
        # Clean bucket
        clean_bucket(job_id,bucket_name)
        
        
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

