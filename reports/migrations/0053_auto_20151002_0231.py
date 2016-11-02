# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0052_auto_20150930_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrationarea',
            name='domain',
            field=models.ForeignKey(related_name='domain_administrationarea', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='domain',
            field=models.ForeignKey(related_name='domain_casedefinition', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='domain',
            field=models.ForeignKey(related_name='domain_report', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportcomment',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportcomment', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportimage', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstate',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstate', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstateunique',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstateunique', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='domain',
            field=models.ForeignKey(related_name='domain_reporttype', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='spreadsheetresponse',
            name='domain',
            field=models.ForeignKey(related_name='domain_spreadsheetresponse', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
