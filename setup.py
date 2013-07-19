from setuptools import setup


setup(
    name='djcache',
    version='0.1',
    description="Auto caching for django's sql queries with redis",
    py_modules=['djcache'],
    install_requires=["Django>=1.3", "msgpack-python>=0.3.0", "redis>=2.7.5"],
    author='Alexander Orlov')
