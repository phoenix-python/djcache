"""
Djcache adds auto caching to your django application.
It's implicit(so You don't need to rewrite code to use it) and easy to install.
Currently supports only mysql as database and redis as cache engine
"""
import json
import msgpack
import hashlib
import datetime

import redis
from django.conf import settings
from django.db import connection, models
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.signals import post_save, post_delete
from django.db.models.sql.datastructures import EmptyResultSet


__version__ = '0.0.1'
UDF_INVALIDATION = 0
SIGNAL_INVALIDATION = 1
ACTIVE_QUERIES = 'active_queries'


DJCACHE_OPTIONS = getattr(settings, 'DJCACHE_OPTIONS', {})
REDIS_CLIENT = redis.Redis(**DJCACHE_OPTIONS.get('REDIS_SETTINGS', {}))
NATIVE_SQL = SQLCompiler.execute_sql


def __decode_datetime(obj):
    return (
        datetime.datetime.strptime(obj["as_str"], "%Y%m%dT%H:%M:%S.%f")
        if b'__datetime__' in obj else obj) 


def __encode_datetime(obj):
    return (
        {'__datetime__': True, 'as_str': obj.strftime("%Y%m%dT%H:%M:%S.%f")}
        if isinstance(obj, datetime.datetime) else obj)


def cached_sql_execution(self, state):
    """
    Replacement of django internal execute_sql function
    Caching engine for select db requests
    """
    try:
        sql = self.as_sql()
        sql = sql[0] % sql[1]
        call_native = not sql.startswith('SELECT')
    except EmptyResultSet:
        call_native = True

    if call_native:
        return NATIVE_SQL(self, state)

    db_name = settings.DATABASES[self.using]['NAME']
    table_key = '%s.%s' % (
        db_name, ''.join(map(':{0}:'.format, sorted(self.query.tables))))

    query = dict(db=db_name, sql=sql)
    key = hashlib.md5(json.dumps(query)).hexdigest()

    if REDIS_CLIENT.sismember(table_key, key):
        data = REDIS_CLIENT.get(key)
        if data:
            return iter(msgpack.loads(
                data, use_list=False, object_hook=__decode_datetime))

    data = NATIVE_SQL(self, state)
    if data is None:
        return None
    data = list(data)
    ttl = DJCACHE_OPTIONS.get('TTL', 24 * 60 * 60)
    REDIS_CLIENT.setex(key, msgpack.dumps(data, default=__encode_datetime), ttl)
    REDIS_CLIENT.sadd(ACTIVE_QUERIES, table_key)
    REDIS_CLIENT.sadd(table_key, key)
    return iter(data)


def invalidation_signal(sender, **kwargs):
    for collection in REDIS_CLIENT.smembers(ACTIVE_QUERIES):
        if ":{0}:".format(sender._meta.db_table) in collection:
            REDIS_CLIENT.delete(collection)


def create_invalidation_triggers():
    """
    Creates invalidation triggers in database
    Currently works only with MySQL
    """
    def _safe_call(cursor, sql):
        try:
            cursor.execute(sql)
        except Exception as exc:
            code, msg = exc
            print msg

    trigger = """
        create trigger %(name)s %(event)s on %(table)s for each row
        select if(@enable_cache=FALSE, 0, sys_exec(
            concat('redis-cli smembers active_queries | grep :%(table)s: | grep ^', DATABASE(), ' | xargs redis-cli del')))
        into @val;"""

    tables = [x._meta.db_table for x in models.get_models()]
    events = ['before insert', 'after update', 'after delete']
    cursor = connection.cursor()

    for table in tables:
        for event in events:
            context = dict(table=table, action=event.split()[1], event=event)
            context['name'] = 'invalidation_%(table)s_%(action)s' % context
            _safe_call(cursor, "drop trigger %(name)s;" % context)
            _safe_call(cursor, trigger % context)
    cursor.close()


def patch():
    """
    Adds caching to django's sql compiler and creates invalidation triggers
    """
    if DJCACHE_OPTIONS.get('DISABLE_CACHE'):
        return
    SQLCompiler.execute_sql = cached_sql_execution

    if DJCACHE_OPTIONS.get("INVALIDATION", 0) == SIGNAL_INVALIDATION:
        for model in models.get_models():
            post_save.connect(invalidation_signal, sender=model)
            post_delete.connect(invalidation_signal, sender=model)
