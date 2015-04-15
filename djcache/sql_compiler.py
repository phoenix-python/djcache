"""
Djcache adds auto caching to your django application.
It's implicit(so You don't need to rewrite code to use it) and easy to install.
"""
import hashlib
import itertools
import json
import time

from django.conf import settings
from django.db import models
from django.db.models.signals import (
    post_save,
    post_delete,
)
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.datastructures import EmptyResultSet
import redis

from djcache.serializers import (
    dump_sql_result,
    load_sql_result,
)


DJCACHE_OPTIONS = getattr(settings, 'DJCACHE_OPTIONS', {})
REDIS_CLIENT = redis.Redis(**DJCACHE_OPTIONS.get('REDIS_SETTINGS', {}))
NATIVE_SQL = SQLCompiler.execute_sql
ACTIVE_QUERIES_KEY = 'active_queries'


def cache_key(db_name, sql):
    query = dict(db=db_name, sql=sql)
    return hashlib.md5(json.dumps(query)).hexdigest()


def validation_cache_key(db_name, table_names):
    tables = ''.join(map(':{0}:'.format, sorted(table_names)))
    return '{0}.{1}'.format(db_name, tables)


def fetch_from_cache(key, validation_key):
    """Fetch from cache and check that cached db result is still valid"""
    cached_data, timestamp = load_sql_result(REDIS_CLIENT.get(key))
    if int(REDIS_CLIENT.hget(validation_set_key, key)) == timestamp:
        return cached_data


def set_cache(key, validation_key, db_result):
    """Store db result in redis and mark it as valid in validation set"""
    ttl = DJCACHE_OPTIONS.get('TTL', 24 * 60 * 60)
    now = int(time.time())
    data = [list(db_result), now]

    REDIS_CLIENT.setex(key, data, ttl)
    REDIS_CLIENT.hset(validation_key, key, now)
    REDIS_CLIENT.sadd(ACTIVE_QUERIES_KEY, validation_key)


def cached_sql_execution(self, state):
    """
    Replacement of django internal execute_sql function
    Caching engine for select db requests
    """
    try:
        sql = self.as_sql()
        sql = sql[0] % sql[1]
        call_native = (
            self.using in DJCACHE_OPTIONS.get('BLACKLISTED_CONNECTIONS', []) or
            not sql.startswith('SELECT'))
    except EmptyResultSet:
        call_native = True

    if call_native:
        return NATIVE_SQL(self, state)

    db_name = settings.DATABASES[self.using]['NAME']
    key = cache_key(db_name, sql)
    validation_key = validation_cache_key(db_name, self.query.tables)

    cached_data = fetch_from_cache(key, validation_key)
    if cached_data is not None:
        return iter(cached_data)

    db_result = NATIVE_SQL(self, state)
    if db_result is None:
        return None

    data_to_save, data_to_return = itertools.tee(db_result)
    set_cache(key, validation_key, data_to_save)
    return data_to_return


def invalidation_signal(sender, **kwargs):
    """Invalidate all possible cached sql queries related to given table"""
    for collection in REDIS_CLIENT.smembers(ACTIVE_QUERIES_KEY):
        if ":{0}:".format(sender._meta.db_table) in collection:
            REDIS_CLIENT.delete(collection)


def patch():
    """Replace django's native sql compiler and bind signals"""
    if DJCACHE_OPTIONS.get('DISABLE_CACHE', False):
        return

    SQLCompiler.execute_sql = cached_sql_execution

    if not DJCACHE_OPTIONS.get('DISABLE_INVALIDATION', False):
        for model in models.get_models():
            post_save.connect(invalidation_signal, sender=model)
            post_delete.connect(invalidation_signal, sender=model)
