# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0089_reporttype_user_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='first_image_thumbnail_url',
            field=models.CharField(max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='parent_type',
            field=models.CharField(default=b'GENERAL', max_length=255, null=True, blank=True, choices=[(b'GENERAL', b'General'), (b'MERGE', b'Merge')]),
            preserve_default=True,
        ),
    ]
