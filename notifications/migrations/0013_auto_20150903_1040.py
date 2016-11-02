# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0012_notificationtemplate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationtemplate',
            name='data',
        ),
        migrations.AddField(
            model_name='followup',
            name='disabled',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='trigger_delay_days',
            field=models.IntegerField(max_length=5, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='trigger_notify_follow_up',
            field=models.ForeignKey(related_name='late_follow_up', blank=True, to='notifications.NotificationTemplate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='trigger_pattern',
            field=models.CharField(max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
    ]
