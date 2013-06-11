from distutils.core import setup


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with redis",
    py_modules=['djcache'],
    requires=['django', 'redis'],
    author='Alexander Orlov')
