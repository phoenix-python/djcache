import os
import sys
import json

from distutils.core import setup
from setuptools.command.install import install as DistutilsInstall


class MakeInstall(DistutilsInstall):
    PASSWORD_FILE = '/tmp/mysql.json'

    def run(self):
        try:
            password = json.loads(open(self.PASSWORD_FILE).read())['password']
        except IOError, KeyError:
            password = None

        password = '-p' if password is None else '--password="%s"' % password
        
        status = os.system(
            """mysql -u root %s -e "select sys_exec('id');"  """ % password)
        if status == 0:
            DistutilsInstall.run(self)
        else:
            cmds = [
                'sudo apt-get install gcc make libmysqlclient-dev',
                'sudo gcc -fpic -Wall -I/usr/include/mysql -I. -shared lib_mysqludf_sys.c -o /usr/lib/mysql/plugin/lib_mysqludf_sys.so',
                'mysql -u root %s -e "DROP FUNCTION IF EXISTS sys_exec"' % password,
                """mysql -u root %s -e "CREATE FUNCTION sys_exec RETURNS int SONAME 'lib_mysqludf_sys.so'" """ % password,
            ]
            for cmd in cmds:
                os.system(cmd)
            status = os.system(
                """mysql -u root %s -e "select sys_exec('id');"  """ % password)
            if status == 0:
                DistutilsInstall.run(self)


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with mysql and redis",
    py_modules=['djcache'],
    cmdclass={'install': MakeInstall},
    requires=['django', 'redis', '_mysql'],
    author='Alexander Orlov')
