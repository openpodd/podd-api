
import json

import datetime
from django_redis import get_redis_connection


def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()


def publish(channel, data):
    r = get_redis_connection()
    r.publish(channel, json.dumps(data, default=default))
