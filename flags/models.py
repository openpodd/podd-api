
from django.conf import settings
from django.db import models

from common.constants import PRIORITY_CHOICES
from reports.models import ReportState

# Deprecate
class Flag(models.Model):
    comment = models.OneToOneField('reports.ReportComment', related_name='flags')
    flag_owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='flag_owners')
    priority = models.PositiveIntegerField(default=0, choices=PRIORITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey('reports.ReportState', related_name='flag_state', null=True, blank=True)



    def save(self, *args, **kwargs):
        super(Flag, self).save(*args, **kwargs)

        report = self.comment.report
        report.priority = self.priority
        report.save()
        #report.save(update_fields=['priority'])
