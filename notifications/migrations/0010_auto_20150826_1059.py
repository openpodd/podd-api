# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0037_auto_20150826_1059'),
        ('accounts', '0030_authority_created_by'),
        ('notifications', '0009_remove_notificationtemplate_reporter_feedback'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowUp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('deadline', models.DateField(null=True, blank=True)),
                ('notified', models.BooleanField(default=False)),
                ('late_notified', models.BooleanField(default=False)),
                ('responsed', models.BooleanField(default=False)),
                ('authority', models.ForeignKey(related_name='follow_up_authority', to='accounts.Authority')),
                ('report', models.ForeignKey(to='reports.Report')),
                ('template', models.ForeignKey(related_name='follow_up_template', to='notifications.NotificationTemplate')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='notificationauthority',
            name='is_deleted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='notificationauthority',
            unique_together=set([]),
        ),
    ]
