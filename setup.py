import os
import sys
from distutils.core import setup
from setuptools.command.install import install as DistutilsInstall


class MakeInstall(DistutilsInstall):
    def run(self):
        password = os.environ.get('MYSQL_PASSWORD')
        cmds = [
            'sudo apt-get install gcc make libmysqlclient-dev',
            'sudo gcc -fpic -Wall -I/usr/include/mysql -I. -shared lib_mysqludf_sys.c -o /usr/lib/mysql/plugin/lib_mysqludf_sys.SONAME',
            'mysql -u root %s -e "DROP FUNCTION IF EXISTS sys_exec"' % (
                '-p' if password is None else '--password="%s"' % password),
            """mysql -u root %s -e "CREATE FUNCTION sys_exec RETURNS int SONAME 'lib_mysqludf_sys.so'" """ % (
                '-p' if password is None else '--password="%s"' % password)]
        for cmd in cmds:
            os.system(cmd)
        DistutilsInstall.run(self)


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with mysql and redis",
    py_modules=['djcache'],
    cmdclass={'install': MakeInstall},
    requires=['django', 'redis', '_mysql'],
    author='Alexander Orlov')
