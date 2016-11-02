# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0066_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcomment',
            name='status',
            field=models.IntegerField(default=1, max_length=100, choices=[(1, b'Publish'), (-1, b'Delete')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportlike',
            name='status',
            field=models.IntegerField(default=1, max_length=100, choices=[(1, b'Publish'), (-1, b'Delete')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportmetoo',
            name='status',
            field=models.IntegerField(default=1, max_length=100, choices=[(1, b'Publish'), (-1, b'Delete')]),
            preserve_default=True,
        ),
    ]
