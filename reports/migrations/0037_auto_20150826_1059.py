# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0036_administrationarea_authority'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='updated_by',
            field=models.ForeignKey(related_name='report_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportcomment',
            name='state',
            field=models.ForeignKey(related_name='report_comment_state', blank=True, to='reports.ReportState', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='created_by',
            field=models.ForeignKey(related_name='report_created_by', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
