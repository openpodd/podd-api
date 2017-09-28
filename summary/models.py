from django.db import models

# Create your models here.
from common.models import DomainMixin, AbstractCachedModel
from accounts.models import Authority

class AggregateReport(AbstractCachedModel, DomainMixin):
    name = models.CharField(max_length=500)
    module = models.CharField(max_length=250)
    filter_definition = models.TextField(default='', blank=True)
    authorities = models.ManyToManyField(Authority, related_name='aggregate_report_authority', null=True, blank=True)


