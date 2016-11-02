from elasticsearch import Elasticsearch
from django.conf import settings

def get_elasticsearch_instance():
    return Elasticsearch(settings.HAYSTACK_CONNECTIONS['default']['URL'])
