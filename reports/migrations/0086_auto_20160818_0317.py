# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0085_auto_20160523_0832'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcomment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportcomment',
            name='updated_by',
            field=models.ForeignKey(related_name='comment_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportcomment',
            name='created_by',
            field=models.ForeignKey(related_name='comment_created_by', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
