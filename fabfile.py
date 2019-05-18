from fabric import task, Connection
import os
import json
from pprint import pprint
dirPath = os.path.dirname(os.path.realpath(__file__))
with open('settings.json') as f:
    settings = json.load(f)
pprint(settings['environments'])
@task
def local(context):
    context.name = 'local'
    context.host = '172.28.128.7'
    context.user = 'vagrant'
    context.connect_kwargs.password = 'vagrant'

@task
def production(context):
    context.name = 'production'
    context.host = ''
    context.user = ''
    context.connect_kwargs.key_filename = "c:\\Users\\szabacsik\\.ssh\\id_ed25519.pub"

@task
def update(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('apt update')
        conn.sudo('apt upgrade -y')
        conn.sudo('apt full-upgrade -y')

@task
def installPackages(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('apt install curl -y')

@task
def restart(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('sync && reboot')

@task
def addWorker(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('id -u worker &>/dev/null || useradd -m -s /bin/bash -U worker -u 1000')
        conn.sudo('echo worker:worker | chpasswd')
        conn.sudo('usermod -aG www-data worker')
        conn.sudo('usermod -aG docker worker')
        conn.sudo('echo "worker ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers')

@task
def dockerInstall(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('apt install curl -y')
        conn.sudo('curl -fsSL https://get.docker.com -o get-docker.sh')
        conn.sudo('chmod +x get-docker.sh')
        conn.sudo('./get-docker.sh')

@task
def dockerStop(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('docker kill $(docker ps -q)')

@task
def test(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.run('whoami')
        conn.run('uname -a')
        conn.run('uptime')

@task
def disableRootLogin(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('sed -i -e \'s/PermitRootLogin yes/PermitRootLogin no/g\' /etc/ssh/sshd_config')
        conn.sudo('service ssh restart')
