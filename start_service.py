import os
import sys
import requests
import boto3
import paramiko
import subprocess
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from colored import fg, attr

import settings

if __name__ == '__main__':
    service_name = sys.argv[1]
    os.system(f'git clone git@github.com:windevel/base-server.git ../{service_name}')

    headers = {'Authorization': f'token {settings.GIT_TOKEN}'}
    data = {'name': service_name, 'private': True, }
    r = requests.post('https://api.github.com/user/repos', headers=headers, json=data).json()
    http_url = r['clone_url']
    ssh_url = r['ssh_url']
    owner = r['owner']['login']
    os.system(f'cd {service_name} && rm -rf .git && git init && git remote add origin {http_url}'
              ' && git add . && git commit -m "Initial commit" && git push origin master')

    ec2 = boto3.resource(
        'ec2',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    instance = ec2.create_instances(
        ImageId=settings.EC2_IMAGE_ID,
        SecurityGroupIds=settings.EC2_SECURITY_GROUPS,
        MaxCount=1,
        MinCount=1,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': f'{service_name}'
                    },
                ]
            },
        ]
    )[0]
    print('Sever is starting up...')
    while True:
        instance = list(ec2.instances.filter(Filters=[
            {'Name': 'instance-id', 'Values': [instance.instance_id]}
        ]))[0]
        if instance.state['Code'] == 16:
            break
        time.sleep(10)

    server_ip = instance.public_ip_address
    host_key = None
    while not host_key:
        print('key scan..')
        result = subprocess.run(['ssh-keyscan', server_ip], stdout=subprocess.PIPE)
        host_key = result.stdout.decode('utf-8').strip('\n')
        time.sleep(3)

    os.system(f'''echo "{host_key}" >> ~/.ssh/known_hosts''')

    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
    ssh.connect(server_ip, username='ubuntu', key_filename=os.path.expanduser(settings.SSH_KEY_PATH))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f'ssh-keygen -t rsa -C "{settings.SSH_EMAIL}" -N "" -f /home/ubuntu/.ssh/id_rsa')
    ssh_key = None
    while not ssh_key:
        print('server key scan...')
        stdin, stdout, stderr = ssh.exec_command('cat /home/ubuntu/.ssh/id_rsa.pub')
        ssh_key = stdout.read().decode(sys.stdout.encoding).strip('\n')
        time.sleep(3)

    data = {'title': 'server', 'key': ssh_key, 'read_only': True}
    r = requests.post(f'https://api.github.com/repos/{owner}/{service_name}/keys', headers=headers, json=data)
    stdin, stdout, stderr = ssh.exec_command('ssh-keyscan github.com')
    git_key = stdout.read().decode(sys.stdout.encoding)

    sftp = ssh.open_sftp()
    file_handle = sftp.file('/home/ubuntu/.ssh/known_hosts', mode='a+', bufsize=1)
    file_handle.write(git_key)
    print('server git clone..')
    stdin, stdout, stderr = ssh.exec_command(f'cd /home/ubuntu/service && git clone {ssh_url} .')
    file_handle = sftp.file('/home/ubuntu/service/service_settings.py', mode='w', bufsize=1)
    file_handle.write(f"SERVICE_NAME = '{service_name}'")
    file_handle.flush()

    conn = psycopg2.connect(dbname=settings.DB_NAME, user=settings.DB_USER, password=settings.DB_PASSWORD, host=settings.DB_HOST)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE {service_name};')

    ssh.exec_command('sudo service supervisor restart')

    print('\n', 'Server IP:', fg('light_green_3'), attr('bold'), server_ip, attr('reset'))
    print('Admin address:', fg('light_green_3', attr('bold'), f'http://{server_ip}/admin', attr('reset')))
    print(f'Git ssh url: {ssh_url}')
    print(f'Git http url: {http_url}')

