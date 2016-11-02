from common.decorators import domain_celery_task
from feed.functions import purge_all_expired_cache
from podd.celery import DomainTask, app


@app.task
def purge_all_expired_cache_task():
    purge_all_expired_cache()
