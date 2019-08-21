from fabric import task, Connection
from invoke import call
import requests

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


# https://stackoverflow.com/questions/49839028/how-to-upgrade-docker-compose-to-latest-version
@task
def dockerComposeInstall(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        r = requests.get('https://api.github.com/repos/docker/compose/releases/latest')
        data = r.json()
        latest_version = data['name']
        destionation = '/usr/local/bin/docker-compose'
        conn.sudo('curl -L https://github.com/docker/compose/releases/download/%s/docker-compose-$(uname -s)-$(uname -m) -o %s' % (latest_version, destionation))
        conn.sudo('chmod 755 %s' % destionation)


@task
def dockerComposeRemove(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.sudo('apt purge docker-compose')
        destionation = '/usr/local/bin/docker-compose'
        conn.sudo('rm -rf %s' % destionation)


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

# https://stackoverflow.com/questions/3557037/appending-a-line-to-a-file-only-if-it-does-not-already-exist
# docker exec -it -u0 database /bin/bash -lc "grep -qxF 'bind-address = 0.0.0.0' /etc/my.cnf || echo 'bind-address = 0.0.0.0' >> /etc/my.cnf"
@task
def addLineToFileIfNotExist(context, line, file, container=None):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        command = 'grep -qxF \'%s\' %s || echo \'%s\' >> %s' %(line, file, line, file)
        if not (container is None):
            command = 'docker exec -i -u0 %s /bin/bash -lc "%s"' % (container, command)
        else:
            command = 'sh -c \'%s\'' % command
        conn.sudo(command, warn=True)


@task(pre=[call(addLineToFileIfNotExist, line='8.8.8.8', file='/etc/resolv.conf'), call(addLineToFileIfNotExist, line='9.9.9.9', file='/etc/resolv.conf'), call(addLineToFileIfNotExist, line='8.8.4.4', file='/etc/resolv.conf')])
def addNameServers(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        command = "sh -c \'sed -i -e \"s/options edns0/#options edns0/g\" /etc/resolv.conf\'"
        conn.sudo(command, warn=True)

@task(pre=[call(addLineToFileIfNotExist, line="bind-address = 0.0.0.0", file="/etc/my.cnf", container="database")])
def mysqlAllowNetworkAccess(context):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        container = "database"
        sql = 'CREATE USER IF NOT EXISTS \'root\'@\'%\' IDENTIFIED BY \'PASSWORD\';'
        command = "docker exec -i %s mysql -u root --password=PASSWORD -e \"%s\"" % (container, sql)
        conn.sudo(command)
        sql = 'GRANT ALL PRIVILEGES ON *.* TO \'root\'@\'%\' WITH GRANT OPTION;'
        command = "docker exec -i %s mysql -u root --password=PASSWORD -e \"%s\"" % (container, sql)
        conn.sudo(command)
        sql = 'FLUSH PRIVILEGES;'
        command = "docker exec -i %s mysql -u root --password=PASSWORD -e \"%s\"" % (container, sql)
        conn.sudo(command)

@task
def dockerComposeUp(context, composeYmlDirectory="/home/worker"):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.run('cd %s && docker-compose up --detach' % composeYmlDirectory)

@task
def dockerComposeUpForced(context, composeYmlDirectory="/home/worker"):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.run('cd %s && docker-compose up --detach --force-recreate' % composeYmlDirectory)

@task
def dockerComposeDown(context, composeYmlDirectory="/home/worker"):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.run('cd %s && docker-compose down' % composeYmlDirectory)

@task
def dockerComposePull(context, composeYmlDirectory="/home/worker"):
    with Connection(context.host, context.user, connect_kwargs=context.connect_kwargs) as conn:
        conn.run('cd %s && docker-compose pull' % composeYmlDirectory)
