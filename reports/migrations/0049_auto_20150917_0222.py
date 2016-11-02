# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0048_reporttype_summary_template'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reporttype',
            options={'ordering': ['weight', 'name']},
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='follow_days',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='followable',
            field=models.NullBooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='version',
            field=models.IntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='weight',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
