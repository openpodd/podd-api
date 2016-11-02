import datetime
import json

from accounts.models import User

from haystack import indexes


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    username = indexes.CharField(model_attr='username', indexed=False)
    first_name = indexes.CharField(model_attr='first_name')
    last_name = indexes.CharField(model_attr='last_name')
    full_name = indexes.CharField(model_attr='get_full_name')

    domain = indexes.IntegerField(model_attr='domain__id', indexed=True, stored=True)


    def get_model(self):
        return User
