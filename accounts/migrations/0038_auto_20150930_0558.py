# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('accounts', '0037_authority_deep_subscribes'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='domain',
            field=models.ForeignKey(default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='authorityinvite',
            name='domain',
            field=models.ForeignKey(default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='domain',
            field=models.ForeignKey(default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userdevice',
            name='domain',
            field=models.ForeignKey(default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
