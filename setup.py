import os
import sys
from distutils.core import setup


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with mysql and redis",
    py_modules=['djcache'],
    install_requires=['redis', 'django', 'MySQL-python'],
    author='Alexander Orlov')
