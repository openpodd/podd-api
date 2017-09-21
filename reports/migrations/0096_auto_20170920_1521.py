# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0095_reporttype_report_post_save'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporttype',
            name='notification_buffer',
            field=models.FloatField(help_text=b'Radius of buffer that use to find intersects authorities', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reporttype',
            name='notification_type',
            field=models.IntegerField(default=0, help_text=b'Notify authorities based on report location', choices=[(0, b'Notify by lookup authority based on admin_area'), (1, b'Notify by lookup authorities based on geometry intercepts with report locaation')]),
            preserve_default=True,
        ),
    ]
