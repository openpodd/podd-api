from .base import *

import os
env = os.environ.get

SECRET_KEY = env('PODD_DJANGO_SECRET_KEY') or 'secret12346789012345679012345678'

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['*']

NOTIFICATION_DISABLED = env('NOTIFICATION_DISABLED') or True

EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

postgres = env('PODD_DB_HOST') or (env('POSTGRES_PORT_5432_TCP_ADDR') and 'postgres')
if postgres:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": env("PODD_DB_NAME") or env("POSTGRES_ENV_POSTGRES_USER") or 'postgres',
            "USER": env("PODD_DB_NAME") or env("POSTGRES_ENV_POSTGRES_USER") or 'postgres',
            "PASSWORD": env("PODD_DB_PASSWORD") or env("POSTGRES_ENV_POSTGRES_PASSWORD") or 'secret1234',
            "HOST": postgres,
            "PORT": env('PODD_DB_PORT') or '',
        }
    }

ESPER_CONNECTION_URL = 'http://%s:8080/podd-cep/' % (env('PODD_CEP_HOST') or 'cep')
ESPER_RESPONSE_BASE_URL = 'http://api:8000/'

raven_dsn = env('PODD_RAVEN_DSN') or ''
if raven_dsn:
    RAVEN_CONFIG = {
        'dsn': raven_dsn,
    }

NEO4J_CONNECTION_URL = 'bolt://%s' % (env('PODD_GRAPHDB_HOST') or 'neo4j')

redis = env('PODD_REDIS_HOST') or (env('REDIS_PORT_6379_TCP_ADDR') and 'redis')
if not redis:
    raise Exception('Error: REDIS_PORT_6379_TCP_ADDR (or PODD_REDIS_HOST) is undefined, did you forget to `--link` a redis container?')

redis_password = env('PODD_REDIS_PASSWORD') or ''
redis_port = env('PODD_REDIS_PORT') or '6379'
redis_db = env('PODD_REDIS_DB') or '0'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:%s/%s" % (redis, redis_port, redis_db)
    }
}
BROKER_URL = CACHES['default']['LOCATION']

CACHEOPS_REDIS = {
    'host': redis,
    'port': redis_port,
    'db': env('PODD_REDIS_CACHEOPS_DB') or '0'
}

elasticsearch = env('PODD_ES_HOST') or (env('ELASTICSEARCH_PORT_9200_TCP_ADDR') and 'elasticsearch')
elasticsearch_port = env('PODD_ES_PORT') or 9200
elasticsearch_index_name = env('PODD_ES_INDEX_NAME') or 'haystack'
if elasticsearch:
    HAYSTACK_CONNECTIONS.update({
        'default': {
            'ENGINE': 'podd.backends.ConfigurableElasticSearchEngine',
            'URL': 'http://%s:%s/' % (elasticsearch, elasticsearch_port),
            'INDEX_NAME': elasticsearch_index_name,
        },
    })

    if TESTING:
        HAYSTACK_CONNECTIONS.update({
            'default': {
                'ENGINE': 'podd.backends.ConfigurableElasticSearchEngine',
                'URL': 'http://%s:%s/' % (elasticsearch, elasticsearch_port),
                'INDEX_NAME': 'test_index'
            }
        })

SIMULATION_MODE = env('PODD_SIMULATION_MODE') or False
CELERY_ALWAYS_EAGER = env('PODD_CELERY_ALWAYS_EAGER') or False
CELERY_EAGER_PROPAGATES_EXCEPTIONS = env('PODD_CELERY_EAGER_PROPAGATES_EXCEPTIONS') or False

MINUTES_PER_DAY = 24*60
AUTHORITY_INVITE_EXPIRE_DAYS = 30
NOTIFICATION_THRESHOLDS = {
    'delayed_follow_up_interval': timedelta(minutes=5),
    'delayed_follow_up_check_period': timedelta(minutes=15),
}

CELERYBEAT_SCHEDULE = {
    'report-follow-up': {
        'task': 'notifications.tasks.send_alert_follow_up',
        'schedule': timedelta(minutes=MINUTES_PER_DAY)
    },
    'delayed-follow-up': {
        'task': 'notifications.tasks.send_delayed_follow_up',
        'schedule': NOTIFICATION_THRESHOLDS['delayed_follow_up_interval'],
    },
    'purge-all-expired-cache': {
        'task': 'feed.tasks.purge_all_expired_cache_task',
        'schedule': timedelta(days=1),
    }
}
