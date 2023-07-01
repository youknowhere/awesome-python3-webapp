# -*- coding: utf-8 -*-

# fabfile.py
import os, re
from datetime import datetime

# 导入Fabric API
from fabric.api import *

# 服务器登录用户名:
env.user = 'fan'
# sudo用户为root:
env.sudo_user = 'root'
# 服务器地址，可以有多个，依次部署:
# env.hosts = ['127.0.0.1']
env.host_string = '192.168.5.128'
# 服务器MySQL用户名和口令:
db_user = 'www-data'
db_password = 'www-data'

_TAR_FILE = 'dist-awesome.tar.gz'

_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/awesome'

def build():
    includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
    excludes = ['test', '.*', '*.pyc', '*.pyo']
    local('del /F dist\%s' % _TAR_FILE)

    with lcd(os.path.join(os.path.abspath('.'), 'www')):
        cmd = ['tar', '-czvf', '..\dist\%s' % _TAR_FILE]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        local(' '.join(cmd))

def deploy():
    new_dir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    run('rm -f %s' % _REMOTE_TMP_TAR)
    put('dist/%s'%_TAR_FILE, _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        sudo('mkdir %s' % new_dir)
    with cd("%s/%s" % (_REMOTE_BASE_DIR, new_dir)):
        sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)
        sudo('dos2unix app.py')     # 解决windows和linux行尾换行不同问题
        sudo('chmod a+x app.py')    # 使app.py可直接执行
    with cd(_REMOTE_BASE_DIR):
        sudo('rm -rf www')
        sudo('ln -s %s www' % new_dir)
        sudo('chown fan:fan www')
        sudo('chown -R fan:fan %s' % new_dir)
    with settings(warn_only=True):
        sudo('supervisorctl stop awesome')
        sudo('supervisorctl start awesome')
        sudo('/etc/init.d/nginx reload')

