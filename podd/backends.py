
from django.conf import settings

from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from haystack.backends.elasticsearch_backend import ElasticsearchSearchEngine


class ConfigurableElasticBackend(ElasticsearchSearchBackend):

    DEFAULT_SETTINGS = {
        'settings': {
            "analysis": {
                "analyzer": {
                    "default":{
                        "type":"custom",
                        "tokenizer": "thai",
                        "filters": [ "standard","lowercase", "stop" ]
                    }
                },
                "tokenizer": {
                    "haystack_ngram_tokenizer": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                    "haystack_edgengram_tokenizer": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "side": "front"
                    }
                },
                "filter": {
                    "haystack_ngram": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15
                    },
                    "haystack_edgengram": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15
                    }
                }
            }
        }
    }

    def __init__(self, connection_alias, **connection_options):
        super(ConfigurableElasticBackend, self).__init__(
                                connection_alias, **connection_options)
        user_settings = getattr(settings, 'ELASTICSEARCH_INDEX_SETTINGS', self.DEFAULT_SETTINGS)
        if user_settings:
            setattr(self, 'DEFAULT_SETTINGS', user_settings)


class ConfigurableElasticSearchEngine(ElasticsearchSearchEngine):
    backend = ConfigurableElasticBackend
