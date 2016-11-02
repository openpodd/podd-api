
from django.conf import settings
from django.db import models
from accounts.models import Authority

from common.constants import NewsTypeChoices
from common.models import DomainMixin


class News(DomainMixin):
    type = models.CharField(max_length=100, choices=NewsTypeChoices)
    message = models.TextField()
    area = models.ForeignKey('reports.AdministrationArea', null=True, blank=True)
    authority = models.ForeignKey(Authority, null=True, blank=True)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'news'

    def __unicode__(self):
        return '%s: %s' % (self.get_type_display(), self.message)

