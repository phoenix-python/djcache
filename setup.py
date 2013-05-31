import os
import sys
import json

from distutils.core import setup
from setuptools.command.install import install as DistutilsInstall


class MakeInstall(DistutilsInstall):
    def _udf_checker(self):
        checker = """ mysql -u root -p -e "select sys_exec('id');" """
        return os.system(checker) == 0

    def run(self):
        if self._udf_checker():
            DistutilsInstall.run(self)
        else:
            cmds = [
                'sudo apt-get install gcc make libmysqlclient-dev',
                'sudo gcc -fpic -Wall -I/usr/include/mysql -shared udf.c -o /usr/lib/mysql/plugin/udf.so',
                'mysql -u root -p -e "DROP FUNCTION IF EXISTS sys_exec"',
                """mysql -u root -p -e "CREATE FUNCTION sys_exec RETURNS int SONAME 'udf.so'" """]
            for cmd in cmds:
                os.system(cmd)
            if self._udf_checker():
                DistutilsInstall.run(self)


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with mysql and redis",
    py_modules=['djcache'],
    cmdclass={'install': MakeInstall},
    requires=['django', 'redis', '_mysql'],
    author='Alexander Orlov')
