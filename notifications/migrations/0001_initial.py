# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_report_parent'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=200, blank=True)),
                ('type', models.CharField(max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'NEARBY', b'Nearby')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seen_at', models.DateTimeField(null=True, blank=True)),
                ('receive_user', models.ForeignKey(related_name='receive_user', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(to='reports.Report', null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
            bases=(models.Model,),
        ),
    ]
