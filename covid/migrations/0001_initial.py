# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0071_auto_20191120_1156'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0104_reporttype_merge_with_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('qty_new_case', models.IntegerField(default=0)),
                ('qty_new_monitoring', models.IntegerField(default=0)),
                ('qty_ongoing_monitoring', models.IntegerField(default=0)),
                ('qty_acc_finished', models.IntegerField(default=0)),
                ('authority', models.ForeignKey(to='accounts.Authority', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DailySummaryByVillage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('village_no', models.IntegerField()),
                ('low_risk', models.IntegerField(default=0)),
                ('medium_risk', models.IntegerField(default=0)),
                ('high_risk', models.IntegerField(default=0)),
                ('authority', models.ForeignKey(to='accounts.Authority', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MonitoringReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('village_no', models.IntegerField()),
                ('until', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('started_at', models.DateField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('terminate_cause', models.TextField(max_length=255, null=True, blank=True)),
                ('report_latest_state_code', models.TextField(max_length=50, null=True, blank=True)),
                ('authority', models.ForeignKey(to='accounts.Authority', on_delete=django.db.models.deletion.PROTECT)),
                ('report', models.ForeignKey(to='reports.Report', on_delete=django.db.models.deletion.PROTECT)),
                ('reporter', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='dailysummarybyvillage',
            unique_together=set([('authority', 'date', 'village_no')]),
        ),
    ]
