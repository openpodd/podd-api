
import json

import datetime
from django_redis import get_redis_connection


def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()


def publish(channel, data):
    r = get_redis_connection()
    r.publish(channel, json.dumps(data, default=default))


def get_cache(key):
    r = get_redis_connection()

    ''':type r: redis.StrictRedis'''
    return r.get(key)


def set_cache(key, value, expire_in=600):
    r = get_redis_connection()

    ''':type r: redis.StrictRedis'''
    r.set(key, value, expire_in)
