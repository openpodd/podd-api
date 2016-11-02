# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_project_mobile_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_url',
            field=models.TextField(blank=True, null=True, validators=[django.core.validators.URLValidator()]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='thumbnail_avatar_url',
            field=models.TextField(blank=True, null=True, validators=[django.core.validators.URLValidator()]),
            preserve_default=True,
        ),
    ]
