# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_domain_domain'),
        ('reports', '0051_auto_20150922_0746'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='casedefinition',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportcomment',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportimage',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportstate',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reportstateunique',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reporttype',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='spreadsheetresponse',
            name='domain',
            field=models.ForeignKey(related_name='+', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
