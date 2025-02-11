# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0077_auto_20240104_0548'),
        ('reports', '0106_reportaccomplishment_public_showcase'),
        ('notifications', '0029_linemessagegroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='LineMessageGroupStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('invite_number', models.CharField(max_length=10)),
                ('report_type_name', models.CharField(max_length=255, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('authority', models.ForeignKey(related_name='line_message_group_stat_authority', to='accounts.Authority')),
                ('notification', models.ForeignKey(related_name='line_message_group_stat_notification', blank=True, to='notifications.Notification', null=True)),
                ('report', models.ForeignKey(related_name='line_message_group_stat_report', blank=True, to='reports.Report', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RunSQL("create index idx_line_message_group_stat_period on notifications_linemessagegroupstat (year, month, authority_id);"),
    ]

