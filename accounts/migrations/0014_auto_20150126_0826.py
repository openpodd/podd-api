# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_auto_20150123_0456'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='note',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='running_number',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='serial_number',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='avatar_url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='contact',
            field=models.TextField(verbose_name='\u0e17\u0e35\u0e48\u0e2d\u0e22\u0e39\u0e48', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='project_mobile_number',
            field=models.CharField(max_length=100, null=True, verbose_name='\u0e40\u0e1a\u0e2d\u0e23\u0e4c\u0e42\u0e17\u0e23\u0e28\u0e31\u0e1e\u0e17\u0e4c\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='telephone',
            field=models.CharField(max_length=100, verbose_name='\u0e40\u0e1a\u0e2d\u0e23\u0e4c\u0e42\u0e17\u0e23\u0e28\u0e31\u0e1e\u0e17\u0e4c\u0e2a\u0e48\u0e27\u0e19\u0e15\u0e31\u0e27', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='thumbnail_avatar_url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
