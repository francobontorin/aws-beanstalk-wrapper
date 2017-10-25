# Elastic Beanstalk Wraper

AWS Elastic Beanstalk makes it even easier for developers to quickly deploy and manage applications in the AWS Cloud. Developers simply upload their application, and Elastic Beanstalk automatically handles the deployment details of capacity provisioning, load balancing, auto-scaling, and application health monitoring.

# The Solution

By using the AWS Python SDK (https://boto3.readthedocs.io/en/latest/) and a Python Framework (http://flask.pocoo.org/) it is possible to simply configure and deploy multiple applications using Elastic Beanstalk. The webpage runs in a simple server or lambda and can be used to automate the creation of new applications without the need to access AWS console. It leverages AWS Cognito to easily add user sign-in authenticatication through social identity providers such as Facebook, Twitter, or Amazon.


# Architecture

(https://s3.amazonaws.com/bontorin/aws-eb-wrapper-arch.png "Architecture")

# Author

Franco Bontorin 
Solutions Architect

# License

This is under GNU GPL v2

# Date

July 2017
