# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0003_planreport_areas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='domain',
            field=models.ForeignKey(related_name='domain_plan', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='planlevel',
            name='domain',
            field=models.ForeignKey(related_name='domain_planlevel', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='planreport',
            name='domain',
            field=models.ForeignKey(related_name='domain_planreport', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
    ]
