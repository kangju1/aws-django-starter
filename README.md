# aws-django-starter

you have to create a setting.py file in which the 'start_service.py' file resides and set the following variables.  
  
AWS_ACCESS_KEY_ID: (string)  
  your aws access key id

AWS_SECRET_ACCESS_KEY: (string)  
  your aws secret access key

AWS_REGION: (string)  
  your desired region for the server to be created

EC2_SECURITY_GROUPS: (list)   
  the security group ids for the server

GIT_TOKEN: (string)  
  your personal git token. you can generate one from 'https://github.com/settings/tokens'

SSH_KEY_NAME: (string)  
  the aws ssh key pair name with which the aws ec2 instance is going to start.

SSH_KEY_PATH: (string)  
  your local path of the aws ssh key with which the aws ec2 instance is going to start.

SSH_EMAIL: (string)  
  ssh key email for generating one from the ec2 instance
