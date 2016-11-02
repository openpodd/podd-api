# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0012_auto_20141114_0820'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Mention',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seen_at', models.DateTimeField(null=True)),
                ('is_notified', models.BooleanField(default=False)),
                ('comment', models.ForeignKey(related_name='mentions', to='reports.ReportComment')),
                ('mentionee', models.ForeignKey(related_name='mentionees', to=settings.AUTH_USER_MODEL)),
                ('mentioner', models.ForeignKey(related_name='mentioners', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
