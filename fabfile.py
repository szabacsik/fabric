from fabric import task, Connection
from invoke import call

"""
import os
import json
from pprint import pprint
dirPath = os.path.dirname(os.path.realpath(__file__))
with open('settings.json') as f:
    settings = json.load(f)
pprint(settings['environments'])
"""

@task
def local(context):
    context.name = 'local'
    context.host = '192.168.100.100'
    context.user = 'worker'
    context.connect_kwargs.password = 'worker'


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
        conn.sudo('whoami')
        conn.run('uname -a')
        conn.run('uptime')


@task
def disableRootLogin(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('sed -i -e \'s/PermitRootLogin yes/PermitRootLogin no/g\' /etc/ssh/sshd_config')
        conn.sudo('service ssh restart')


@task
def dockerClean(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('docker kill $(docker ps -q)', warn=True)
        conn.sudo('docker rm $(docker ps -a -q)', warn=True)
        conn.sudo('docker rmi $(docker images -a -q)', warn=True)
        conn.sudo('docker system prune -a --force', warn=True)
        conn.sudo('docker ps -a; docker images -a', warn=True)


@task(optional=['id', 'groups'])
def useradd(context, username, id = None, groups = None):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        result = conn.sudo('id -u %s' % username, warn=True, hide='both')
        exists = result.ok
        if exists:
            print('Aborting. Username \'%s\' already exists.' % username)
            return
        user_add_command = 'useradd --create-home --shell /bin/bash --user-group'
        if not (id is None):
            user_add_command += ' --uid %s' % id
        if not (groups is None):
            groups = groups.split(',')
            user_add_command += ' --groups %s' % ','.join(groups)
        user_add_command += ' %s' % username
        conn.sudo(user_add_command)


@task
def userdel(context, username):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('userdel -r %s --force' % username)


# http://docs.pyinvoke.org/en/latest/api/tasks.html
@task(pre=[call(useradd, username='worker', id='1000', groups='docker')])
def addWorker(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('bash -c \'echo worker:worker | chpasswd\'', warn=True)
        conn.sudo('chmod +w /etc/sudoers')
        conn.sudo('bash -c \'echo "worker ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers\'', warn=True)
        conn.sudo('chmod -w /etc/sudoers')
