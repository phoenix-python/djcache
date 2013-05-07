import os
import sys
from distutils.core import setup
from setuptools.command.install import install as DistutilsInstall


class MakeInstall(DistutilsInstall):
    def run(self):
        os.system('make')
        DistutilsInstall.run(self)
        os.system('rm -rf build')


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with mysql and redis",
    py_modules=['djcache'],
    cmdclass={'install': MakeInstall},
    requires=['django', 'redis', '_mysql'],
    author='Alexander Orlov')
