# -*- encoding: utf-8 -*-
import datetime
import json
import sys
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Authority, User
from reports.models import Report


class MonitoringReport(models.Model):
    authority = models.ForeignKey(Authority, on_delete=models.PROTECT)
    reporter = models.ForeignKey(User, on_delete=models.PROTECT)
    report = models.ForeignKey(Report, on_delete=models.PROTECT)
    village_no = models.IntegerField()
    until = models.DateField()
    active = models.BooleanField(default=True)
    started_at = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)
    terminate_cause = models.TextField(max_length=255, blank=True, null=True)
    name = models.TextField(max_length=255, default="")
    report_latest_state_code = models.TextField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return "%s %s" % (self.id, self.name,)

    @classmethod
    def sync_from_report(cls, instance):
        if not MonitoringReport.objects.filter(report_id=instance.id).exists():
            form_data = json.loads(instance.form_data)
            MonitoringReport.objects.create(
                authority=instance.administration_area.authority,
                reporter=instance.created_by,
                village_no=form_data['village_no'] or 0,
                report=instance,
                started_at=instance.incident_date,
                name=form_data['name'] or '',
                until=instance.incident_date + timedelta(days=settings.COVID_FOLLOWUP_DAYS or 14),
                report_latest_state_code=instance.state.code,
                active=True,
            )
        else:
            monitoring = MonitoringReport.objects.get(report_id=instance.id)
            if monitoring.report_latest_state_code != instance.state.code:
                monitoring.report_latest_state_code = instance.state.code
                monitoring.save()

    @classmethod
    def sync_from_followup(cls, instance):
        form_data = json.loads(instance.form_data)
        parent_id = instance.parent_id
        assert parent_id is not None, "followup report must have parent id"
        monitoring = MonitoringReport.objects.get(report_id=parent_id)
        followup_status = form_data['activity_close']
        if followup_status is None:
            return
        if followup_status.find(settings.COVID_FOLLOWUP_TERMINATE_14_DAYS_PATTERN) != -1 or followup_status.find(
                settings.COVID_FOLLOWUP_TERMINATE_DEPARTURE_PATTERN) != -1 or followup_status.find(
                settings.COVID_FOLLOWUP_CONFIRMED_CASE_PATTERN) != -1:
            monitoring.until = datetime.datetime.now()
            monitoring.terminate_cause = followup_status
            monitoring.active = False
            monitoring.save()


@receiver(post_save, sender=Report)
def covid_monitoring_handler(sender, instance, **kwargs):
    if not settings.COVID_MONITORING_ENABLE:
        return
    if not instance.test_flag:
        try:
            if instance.type.code == settings.COVID_REPORT_TYPE_CODE:
                MonitoringReport.sync_from_report(instance)
            else:
                if instance.type.code == settings.COVID_FOLLOWUP_TYPE_CODE:
                    MonitoringReport.sync_from_followup(instance)
        except:
            print(sys.exc_info()[0])


class DailySummary(models.Model):
    authority = models.ForeignKey(Authority, on_delete=models.PROTECT)
    date = models.DateField()
    qty_new_case = models.IntegerField(default=0)
    qty_new_monitoring = models.IntegerField(default=0)
    qty_ongoing_monitoring = models.IntegerField(default=0)
    qty_acc_finished = models.IntegerField(default=0)

    class Meta:
        unique_together = ("authority", "date")


class DailySummaryByVillage(models.Model):
    authority = models.ForeignKey(Authority, on_delete=models.PROTECT)
    date = models.DateField()
    village_no = models.IntegerField()
    low_risk = models.IntegerField(default=0)
    medium_risk = models.IntegerField(default=0)
    high_risk = models.IntegerField(default=0)

    class Meta:
        unique_together = ("authority", "date", "village_no")


class AuthorityInfo(models.Model):
    authority = models.ForeignKey(Authority, on_delete=models.PROTECT, unique=True)
    line_notify_token = models.TextField(max_length=255, blank=True, null=True)