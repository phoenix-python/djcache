import json
import pickle
import hashlib

import redis
import MySQLdb
from django.conf import settings
from django.db import connection
from django.db.models.sql.compiler import SQLCompiler


DJCACHE_OPTIONS = getattr(settings, 'DJCACHE_OPTIONS', {})
REDIS_CLIENT = redis.Redis(**DJCACHE_OPTIONS.get('REDIS_SETTINGS', {}))
NATIVE_SQL = SQLCompiler.execute_sql


def cached_sql_execution(self, state):
    """
    Replacement of django internal execute_sql function
    Caching engine for select db requests
    """
    sql = self.as_sql()
    sql = sql[0] % sql[1]

    if sql[:6] != 'SELECT' or DJCACHE_OPTIONS.get('DISABLE_CACHE'):
        return NATIVE_SQL(self, state)

    db_name = settings.DATABASES[self.using]['NAME']
    table_key = '%s.%s' % (
        db_name, ''.join(map(lambda x: ':%s:' % x, sorted(self.query.tables))))

    query = dict(db=db_name, sql=sql)
    key = hashlib.md5(json.dumps(query)).hexdigest()

    if REDIS_CLIENT.sismember(table_key, key):
        data = REDIS_CLIENT.get(key)
        if data:
            return iter(pickle.loads(data))

    data = NATIVE_SQL(self, state)
    if data is None:
        return None
    data = list(data)
    ttl = DJCACHE_OPTIONS.get('TTL', 24 * 60 * 60)
    REDIS_CLIENT.setex(key, pickle.dumps(data), ttl)
    REDIS_CLIENT.sadd('active_queries', table_key)
    REDIS_CLIENT.sadd(table_key, key)
    return iter(data)


def create_invalidation_triggers(table):
    """
    Creates invalidation triggers for given table
    """
    trigger = """
        create trigger if not exist
        invalidation_%(table)s_%(action)s %(event)s
        on %(table)s for each row 
        select if(@enable_cache=FALSE, 0, sys_exec(concat(
        'redis-cli smembers active_queries | grep :%(table)s: | grep ^', DATABASE(), ' | xargs redis-cli del')))
        into @val;"""
    events = ['before insert', 'after update', 'after delete']
    cursor = connection.cursor()
    for event in events:
        try:
            cursor.execute(trigger % dict(
                table=table, action='_'.join(event.split()), event=event))
        except MySQLdb.Warning:
            pass
    connection.commit()
    cursor.close()


def patch():
    """
    Adds caching to django's sql compiler and creates invalidation triggers
    """
    for model in DJCACHE_OPTIONS.get('TABLES', []):
        create_invalidation_triggers(model)
    SQLCompiler.execute_sql = cached_sql_execution
