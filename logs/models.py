
import json

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Template, Context


class LogActionManager(models.Manager):
    _cache = {}

    def set_cache(self, action):
        self._cache.setdefault(self.db, {})[action.name] = action

    def get_from_cache(self, key):
        """
        Attempts to retrieve the LogAction from cache, if it fails, loads
        the action into the cache.
        
        @param key : key passed to LogAction.objects.get
        """
        try:
            action = self._cache[self.db][key]
        except KeyError:
            try:
                action = LogAction.objects.get(name=key)
                self._cache.setdefault(self.db, {})[key]=action
            except LogAction.DoesNotExist:
                action = LogAction.objects.create(name=key)
                self._cache.setdefault(self.db, {})[key]=action
        return action


class LogAction(models.Model):
    name = models.CharField(max_length=100, unique=True)
    template = models.TextField(blank=True)

    objects = LogActionManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(LogAction, self).save(*args, **kwargs)
        LogAction.objects.set_cache(self)


class LogItemManager(models.Manager):
    def log_action(self, key, created_by, object1, object2=None, object3=None, data=None):
        action = LogAction.objects.get_from_cache(key)
        entry = self.model(action=action, created_by=created_by, object1=object1)
        
        if object2 is not None:
            entry.object2 = object2
        
        if object3 is not None:
            entry.object3 = object3

        if data is not None:
            entry.data = data

        entry.save()
        return entry


class LogItem(models.Model):
    action = models.ForeignKey(LogAction, related_name='items')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    object_type1 = models.ForeignKey(ContentType, related_name='log_items1')
    object_id1 = models.PositiveIntegerField()
    object1 = GenericForeignKey('object_type1', 'object_id1')

    object_type2 = models.ForeignKey(ContentType, null=True, blank=True, related_name='log_items2')
    object_id2 = models.PositiveIntegerField(null=True)
    object2 = GenericForeignKey('object_type2', 'object_id2')

    serialized_data = models.TextField(blank=True)

    objects = LogItemManager()

    _data = None

    class Meta:
        ordering = ('-created_at', )

    @property
    def data(self):
        if self._data is None and not self.serialized_data is None:
            self._data = json.loads(self.serialized_data)
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self.serialized_data = None

    def save(self, *args, **kwargs):
        if self._data is not None and self.serialized_data is None:
            self.serialized_data = json.dumps(self._data)
        super(LogItem, self).save(*args, **kwargs)

    def render(self):
        action = LogAction.objects.get_from_cache(self.action.name)

        t = Template(action.template)
        c = Context({
            'log_item': self,
        })
        template_rendered = t.render(c)

        return template_rendered
