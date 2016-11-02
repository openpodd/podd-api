from __future__ import absolute_import

import os

from celery import Celery, Task

from django.conf import settings

# set the default Django settings module for the 'celery' program.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'podd.settings.local')

class DomainCelery(Celery):
    pass

app = DomainCelery('podd')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


class DomainTask(Task):
    abstract = True

    def apply_async(self, args=None, kwargs=None, task_id=None, producer=None,
                    link=None, link_error=None, **options):

        from crum import get_current_user

        user_id = None
        user = get_current_user()
        if user and user.id:
            user_id = user.id

        try:
            options['headers']
        except KeyError:
            options['headers'] = {}

        options['headers']['current_user_id'] = user_id

        super(DomainTask, self).apply_async(args, kwargs, task_id, producer, link, link_error, **options)
