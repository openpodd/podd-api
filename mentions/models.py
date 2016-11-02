
from django.conf import settings
from django.db import models
from common.models import DomainMixin


class Mention(DomainMixin):
    comment = models.ForeignKey('reports.ReportComment', related_name='mentions')
    mentioner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='mentioners')
    mentionee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='mentionees')
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    is_notified = models.BooleanField(default=False)
