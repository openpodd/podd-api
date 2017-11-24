# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_domain_timezone'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0097_auto_20171006_0951'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportAccomplishment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(related_name='accomplishment_created_by', to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportaccomplishment', verbose_name=b'Current domain', to='common.Domain')),
                ('report', models.ForeignKey(related_name='accomplishments', to='reports.Report', unique=True)),
                ('updated_by', models.ForeignKey(related_name='accomplishment_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
