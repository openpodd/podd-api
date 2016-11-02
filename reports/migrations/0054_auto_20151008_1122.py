# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0053_auto_20151002_0231'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='parent',
            field=models.ForeignKey(blank=True, to='reports.AdministrationArea', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='administrationarea',
            name='domain',
            field=models.ForeignKey(related_name='domain_administrationarea', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='domain',
            field=models.ForeignKey(related_name='domain_casedefinition', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='domain',
            field=models.ForeignKey(related_name='domain_report', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='priority',
            field=models.PositiveIntegerField(default=0, choices=[(0, b'None'), (1, b'Ignore'), (2, b'OK'), (3, b'Contact'), (4, b'Follow'), (5, b'Case')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportcomment',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportcomment', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportimage', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstate',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstate', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstateunique',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstateunique', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='domain',
            field=models.ForeignKey(related_name='domain_reporttype', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='spreadsheetresponse',
            name='domain',
            field=models.ForeignKey(related_name='domain_spreadsheetresponse', to='common.Domain'),
            preserve_default=True,
        ),
    ]
