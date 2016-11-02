# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0032_auto_20150624_1007'),
        ('accounts', '0022_remove_user_is_volunteer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Authority',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('administration_areas', models.ManyToManyField(related_name='authority_administration_areas', null=True, to='reports.AdministrationArea', blank=True)),
                ('parent', models.ForeignKey(related_name='authority_parent', blank=True, to='accounts.Authority', null=True)),
                ('subscribes', models.ManyToManyField(related_name='subscribes_rel_+', null=True, to='accounts.Authority', blank=True)),
                ('users', models.ManyToManyField(related_name='authority_users', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
