# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0021_auto_20151217_0627'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followup',
            name='domain',
            field=models.ForeignKey(related_name='domain_followup', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='domain',
            field=models.ForeignKey(related_name='domain_notification', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationauthority',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationauthority', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationtemplate', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
    ]
