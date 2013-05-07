import json
import pickle
import hashlib

import redis
import MySQLdb
from django.conf import settings
from django.db import connection, models
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

    if not sql.startswith('SELECT'):
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


def create_invalidation_triggers():
    """
    Creates invalidation triggers for given table
    """
    if DJCACHE_OPTIONS.get('DISABLE_CACHE'):
        return

    def _safe_call(cursor, sql):
        try:
            cursor.execute(sql)
        except MySQLdb.Warning:
            pass

    if 'APP_LABELS' in DJCACHE_OPTIONS:
        tables = [
            x._meta.db_table 
            for x in models.get_models() 
            if x._meta.app_label in DJCACHE_OPTIONS['APP_LABELS']]
    else:
        tables = DJCACHE_OPTIONS.get('TABLES', [])

    trigger = """
        create trigger invalidation_%(table)s_%(action)s %(event)s 
        on %(table)s for each row 
        select if(@enable_cache=FALSE, 0, sys_exec(concat(
        'redis-cli smembers active_queries | grep :%(table)s: | grep ^', DATABASE(), ' | xargs redis-cli del')))
        into @val;"""
    events = ['before insert', 'after update', 'after delete']
    cursor = connection.cursor()
    for table in tables:
        for event in events:
            context = dict(table=table, action=event.split()[1], event=event)
            context['name'] = 'invalidation_%(table)s_%(action)s' % context
            _safe_call(cursor, "drop trigger if exists %(name)s;" % context)
            _safe_call(cursor, trigger % context)
    cursor.close()


def patch():
    """
    Adds caching to django's sql compiler and creates invalidation triggers
    """
    if not DJCACHE_OPTIONS.get('DISABLE_CACHE'):
        SQLCompiler.execute_sql = cached_sql_execution
