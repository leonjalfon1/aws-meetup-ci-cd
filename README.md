# Pipeline Implementation

## 1. Fork the repository

 - Browse to the repository "https://github.com/leonjalfon1/aws-meetup-ci-cd"
 - Fork the repository
 
## 2. Create S3 bucket to store pull request source code

 - Create a buccket called "aws-meetup-sources" with versioning enabled 
 
## 3. Create the required roles and policies

 - Create a new policy called "aws-meetup-lambda" with the permissions below:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "logs:*"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Action": [
                "codepipeline:PutJobSuccessResult",
                "codepipeline:PutJobFailureResult"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
```
 - Create a new role called "aws-meetup-build" to be used by codebuild
 - Create a new role called "aws-meetup-cloudformation" to be used by cloudformation
 - Create a new role called "aws-meetup-codepipeline" to be used by codepipeline
 - Create a new role called "aws-meetup-lambda" with the policy "aws-meetup-lambda-policy" to be used by lambda
 
4. Create lambda function to trigger tests

 - Create a new lambda function called "aws-meetup-runtests"
 - Set "Python 2.7" as runtime
 - Use the role "aws-meetup-lambda"
 - Use the script stored in "config/lambda-runtests.py" 
 
5. Create lambda function to clean pull request bucket

 - Create a new lambda function called "aws-meetup-cleanup"
 - Set "Python 2.7" as runtime
 - Use the role "aws-meetup-lambda"
 - Use the script stored in "config/lambda-cleanup.py"
 
6. Create batch job to run tests

 - TODO

7. Create a codebuild project to build the application

 - You must create it from the codepipeline editor (to use codepipeline as sources)
 - Create a codebuild project called "aws-meetup-build"
 - In the environment section use an ubuntu managed image with node.js runtime
 - Use the existent role called "aws-meetup-build"
 - As buildspec use the file "config/codebuild-build.yml"

 8. Create a codebuild project to build the application

 - You must create it from the codepipeline editor (to use codepipeline as sources)
 - Create a codebuild project called "aws-meetup-cleanup"
 - In the environment section use an ubuntu managed image with base runtime
 - Use the existent role called "aws-meetup-build"
 - As buildspec use the file "config/codebuild-cleanup.yml"
 
 9. Create codebuild project to generate a codepipeline for each pull request

 - Create a codebuild project called "aws-meetup-handler"
 - Select github as provider
 - Select "Repository in my Github account" and grant access to codebuild
 - Select the forked repository
 - Enable "github webhooks" and select the pull request events to trigger the build
 - In the environment section use an ubuntu managed image with base runtime
 - Use the existent role called "aws-meetup-build"
 - As buildspec use the file "config/codebuild-handler.yml"
 - Set a S3 artifact using the bucket "aws-meetup-sources", enable semantic versioning and remove artifact encryption
 
 
 ## Notes:
 
 - To create a codepipeline role you need to create the role from the new codepipeline editor
 - To create a codebuild project with codepipeline sources you must create it from the codepipeline editor