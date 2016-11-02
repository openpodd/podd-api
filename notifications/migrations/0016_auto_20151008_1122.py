# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0015_auto_20151002_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followup',
            name='domain',
            field=models.ForeignKey(related_name='domain_followup', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='domain',
            field=models.ForeignKey(related_name='domain_notification', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationauthority',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationauthority', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationtemplate', to='common.Domain'),
            preserve_default=True,
        ),
    ]
