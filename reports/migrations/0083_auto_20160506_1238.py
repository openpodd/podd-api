# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0082_googlecalendarresponseevent_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='casedefinition',
            name='accumulate',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='casedefinition',
            name='window',
            field=models.TextField(help_text=b'win:ext_timed(date, 7 day)', null=True, verbose_name='EPL window criteria', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='administrationarea',
            name='domain',
            field=models.ForeignKey(related_name='domain_administrationarea', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='animallaboratorycause',
            name='domain',
            field=models.ForeignKey(related_name='domain_animallaboratorycause', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='domain',
            field=models.ForeignKey(related_name='domain_casedefinition', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='casedefinition',
            name='epl',
            field=models.TextField(help_text=b'sickCount > 10, win.areaId = currentEvent.areaId group by win.areaId having (sum(win.sickCount) + sum(win.deadCount)) > 3 (extra params are : win, currentEvent)', verbose_name='EPL where'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='googlecalendarresponse',
            name='domain',
            field=models.ForeignKey(related_name='domain_googlecalendarresponse', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='googlecalendarresponseevent',
            name='domain',
            field=models.ForeignKey(related_name='domain_googlecalendarresponseevent', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='report',
            name='domain',
            field=models.ForeignKey(related_name='domain_report', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportabuse',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportabuse', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportcomment',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportcomment', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportimage',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportimage', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportinvestigation',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportinvestigation', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportlaboratorycase',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportlaboratorycase', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportlaboratoryfile',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportlaboratoryfile', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportlaboratoryitem',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportlaboratoryitem', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportlike',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportlike', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportmetoo',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportmetoo', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstate',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstate', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reportstateunique',
            name='domain',
            field=models.ForeignKey(related_name='domain_reportstateunique', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttype',
            name='domain',
            field=models.ForeignKey(related_name='domain_reporttype', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reporttypecategory',
            name='domain',
            field=models.ForeignKey(related_name='domain_reporttypecategory', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='spreadsheetresponse',
            name='domain',
            field=models.ForeignKey(related_name='domain_spreadsheetresponse', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
    ]
