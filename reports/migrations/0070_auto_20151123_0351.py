# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0005_domain_default_language'),
        ('reports', '0069_report_is_anonymous'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportAbuse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.IntegerField(default=1, max_length=100, choices=[(1, b'Publish'), (-1, b'Delete')])),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportabuse', to='common.Domain')),
                ('report', models.ForeignKey(related_name='report_abuses', to='reports.Report')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reportabuse',
            unique_together=set([('report', 'created_by')]),
        ),
    ]
