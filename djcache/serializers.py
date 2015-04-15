import datetime
import msgpack


def _decode_datetime(obj):
    return (
        datetime.datetime.strptime(obj["as_str"], "%Y%m%dT%H:%M:%S.%f")
        if b'__datetime__' in obj else obj)


def _encode_datetime(obj):
    return (
        {'__datetime__': True, 'as_str': obj.strftime("%Y%m%dT%H:%M:%S.%f")}
        if isinstance(obj, datetime.datetime) else obj)


def dump_sql_result(data):
    return msgpack.dumps(data, default=_encode_datetime, encoding='utf-8')


def load_sql_result(raw_data):
    return msgpack.loads(
        raw_data,
        use_list=False,
        object_hook=_decode_datetime,
        encoding='utf-8')