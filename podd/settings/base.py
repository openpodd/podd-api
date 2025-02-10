# At the top of settings/base.py
# -*- encoding: utf-8 -*-

import os
from os.path import join, abspath, dirname

import raven
from celery.schedules import crontab
from datetime import timedelta

here = lambda *x: join(abspath(dirname(__file__)), *x)
PROJECT_ROOT = here("..", "..")
root = lambda *x: join(abspath(PROJECT_ROOT), *x)

STATIC_ROOT = root('sitestatic')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    root("static"),
)

MEDIA_ROOT = root('media')
MEDIA_URL = '/media/'

"""
Django settings for podd project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    #'opbeat.contrib.django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',

    'test_without_migrations',

    # log
    'raven.contrib.django.raven_compat',

    # libs
    'haystack',
    'leaflet',
    'rest_framework',
    'rest_framework.authtoken',
    'treebeard',
    'corsheaders',
    'django_extensions',
    'taggit',
    'cacheops',

    # apps
    'common',
    'accounts',
    'analysis',
    'areas',
    'feed',
    'flags',
    'logs',
    'monitorings',
    'mentions',
    'notifications',
    'news',
    'reports',
    'supervisors',
    'plans',
    'pages',
    'summary',
    'firebase',
    'dodd',
    'covid',
    'civic',
    'animal',
)

MIDDLEWARE_CLASSES = (
    #'opbeat.contrib.django.middleware.OpbeatAPMMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.SwitchDomainMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

from crum import CurrentRequestUserMiddleware


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

from django.template.base import add_to_builtins
add_to_builtins('plans.templatetags.plans_tags')


ROOT_URLCONF = 'podd.urls'

WSGI_APPLICATION = 'podd.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'management_commands': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}


DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

TEMPLATE_DIRS = (
    # os.path.join(BASE_DIR, 'templates'),
    root('templates'),
)


# Authenticated
LOGIN_REDIRECT_URL = '/supervisors/users/'

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = (
    'accounts.backends.OneDayPasswordModelBackend',
    'django.contrib.auth.backends.ModelBackend'
)


# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'podd.backends.ConfigurableElasticSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# Leaflet
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (13.0, 100.0),
    'DEFAULT_ZOOM': 5,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,
            },
        }
    }
}
BROKER_URL = CACHES['default']['LOCATION']

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

MAX_ATTACH_FILE_COMMENT_SIZE = 10485760

CORS_ORIGIN_ALLOW_ALL = True

# EMAIL
EMAIL_ADDRESS_NO_REPLY = u'ผู้ดูแลระบบ <admin@cmonehealth.org>'

DEFAULT_DOMAIN = {
    'code': 'api.cmonehealth.org, localhost:8000, 127.0.0.1:8000',
    'name': 'cmonehealth'
}

# raven
RAVEN_CONFIG = {
    'dsn': '',
    'site': 'PODD Django',
}

# CELERYBEAT
MINUTES_PER_DAY = 24*60
AUTHORITY_INVITE_EXPIRE_DAYS = 30*12*20
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
    },
    'fetch-dashboard-for-every-days': {
        'task': 'pages.tasks.fetch_dashboard_for_every_days',
        'schedule': crontab(hour=0, minute=0),
    },
    'covid-daily-summarize': {
        'task': 'covid.tasks.daily_summarize',
        'schedule': crontab(hour=0, minute=0), # UTC TIME
    },
    'covid-reporter-followup-notification': {
        'task': 'covid.tasks.notify_reporter_when_no_followup_in_n_days',
        'schedule': crontab(hour=0, minute=30), # UTC TIME
    },
    'covid-daily-summary-notification': {
        'task': 'covid.tasks.daily_notify_authority',
        'schedule': crontab(hour=3, minute=0), # UTC TIME
    },
    'generate_area': {
        'task': 'accounts.tasks.generate_area_files',
        'schedule': crontab(hour=0, minute=30, day_of_week='sunday'), # UTC TIME
    },
    'check_active_authority': {
        'task': 'accounts.tasks.update_active_authority',
        'schedule': crontab(hour=0, minute=0, day_of_week='sunday'), # UTC TIME
    }
}

NOTIFICATION_DISABLED = True

UPDATE_REPORT_STATE_KEY = 'must-override-in-settings-local.py'
ESPER_CONNECTION_URL = ''
ESPER_RESPONSE_BASE_URL = ''
#ESPER_CONNECTION_URL = 'http://127.0.0.1:8080/' # production
#ESPER_RESPONSE_BASE_URL = 'http://127.0.0.1:8000/' # production

NEO4J_CONNECTION_URL = 'http://127.0.0.1:7474/db/data/'

SITE_URL = ''

import sys

TESTING = sys.argv[1:2] == ['test']
SHELLING = sys.argv[1:2] == ['shell'] or sys.argv[1:2] == ['shell_plus']

ADJUST_DATE = True

CACHEOPS_REDIS = {
    'host': 'localhost', # redis-server is on same machine
    'port': 6379,        # default redis port
    'db': 1,             # SELECT non-default redis database
                         # using separate redis db or redis instance
                         # is highly recommended
    'socket_timeout': 3,   # connection timeout in seconds, optional
}

CACHEOPS = {
    # Automatically cache any User.objects.get() calls for 15 minutes
    # This includes request.user or post.author access,
    # where Post.author is a foreign key to auth.User
    'accounts.user': {'ops': 'get', 'timeout': 60*15},

    # Automatically cache all gets and queryset fetches
    # to other django.contrib.auth models for an hour
    'accounts.*': {'ops': ('fetch', 'get'), 'timeout': 60*60},

    # Cache gets, fetches, counts and exists to Permission
    # 'all' is just an alias for ('get', 'fetch', 'count', 'exists')
    #'auth.permission': {'ops': 'all', 'timeout': 60*60},

    # Enable manual caching on all other models with default timeout of an hour
    # Use Post.objects.cache().get(...)
    #  or Tags.objects.filter(...).order_by(...).cache()
    # to cache particular ORM request.
    # Invalidation is still automatic
    #'*.*': {'ops': (), 'timeout': 60*60},
    'reports.report': {'ops': ('get'), 'timeout': 60 * 5},
    'reports.reportimage': {'ops': ('get', 'fetch'), 'timeout': 60 * 5},
    'reports.reporttype': {'ops': ('fetch', 'get'), 'timeout': 60 * 60},
    'reports.administrationarea': {'ops': ('fetch', 'get'), 'timeout': 60 * 60},
    'common.domain': {'ops': ('fetch', 'get'), 'timeout': 60 * 60 * 24},
    'authtoken.token': {'ops': ('get'), 'timeout': 60 * 60},

    # And since ops is empty by default you can rewrite last line as:
    #'*.*': {'timeout': 60*60},
}

if TESTING:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = 'memory'
    NOTIFICATION_DISABLED = True
    CURRENT_DOMAIN_ID = 0
    ADJUST_DATE = False
    # Haystack
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'podd.backends.ConfigurableElasticSearchEngine',
            'URL': 'http://127.0.0.1:9200/',
            'INDEX_NAME': 'test_index',
        },
    }
    CACHES['default']['LOCATION'] = "redis://127.0.0.1:6379/5"
    CACHEOPS = {}

elif SHELLING:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = 'memory'

'''
Firebase settings
'''

FIREBASE_CHAT_API_URL = 'http://example.com/api'
FIREBASE_CHAT_API_KEY = 'REPLACE_WITH_YOUR_KEY'
FIREBASE_SERVICE_ACCOUNT_CERT = ''

# For production only.
#OPBEAT = {
#    'ORGANIZATION_ID': '',
#    'APP_ID': '',
#    'SECRET_TOKEN': '',
#}

SNS_REPORT_ENABLE = False
SNS_REPORT_MAPPING = {
}

COVID_REPORT_TYPE_CODE = "surveillance-covid-19"
COVID_FOLLOWUP_TYPE_CODE = "surveillance-covid-19-followup"
COVID_FOLLOWUP_TERMINATE_14_DAYS_PATTERN = u"สิ้นสุดการติดตาม"
COVID_FOLLOWUP_TERMINATE_DEPARTURE_PATTERN = u"ออกนอกพื้นที่"
COVID_FOLLOWUP_CONFIRMED_CASE_PATTERN = u"ผู้ป่วยยืนยัน"
COVID_FOLLOWUP_TERMINATE_FIELD_NAME = "activity_close"
COVID_FOLLOWUP_DAYS = 14
COVID_FOLLOWUP_NOTIFICATION_ALARM_DAYS = 2
COVID_FOLLOWUP_NOTIFICATION_MESSAGE = u"พบรายงานผู้มีความเสี่ยง Covid-19 ขาดการติดตามเกิน 2 วัน"
COVID_FOLLOWUP_TAG = u"ขาดการติดตามเกิน %s วัน"
COVID_MONITORING_ENABLE = False

LINE_MESSAGING_API_ENDPOINT = 'https://api.line.me/v2/bot/message/push'
LINE_ACCESS_TOKEN = 'OVERRIDE_ME'
LINE_LIFF_COVID_MONITORING_URL = 'https://liff.line.me/1653967705-q4Rrb8x6'
LINE_FOLLOWUP_LABEL = u'ดูรายชื่อคนที่ต้องติดตาม'

DISABLE_CHECK_REPORT_ADMIN_AREA_PERMISSION = False

CHECK_ACTIVE_AUTHORITY_NUMBER_OF_DAYS_TO_INACTIVE = 500
CHECK_ACTIVE_AUTHORITY_SEND_NOTIFICATION_TO_REPORTER = False

CIVIC_REPORT_TYPE_CODE = 'civic'
GOOGLE_STATIC_MAP_API_KEY = ''

LINE_NOTIFICATION_CUTOFF_DATE = '2025-03-31 23:59:59 +07:00'
LINE_NOTIFICATION_TEST_AUTHORITIES = [] # id
LINE_NOTIFICATION_ACCESS_TOKEN = 'OVERRIDE'