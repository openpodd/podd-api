# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0014_auto_20150930_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followup',
            name='domain',
            field=models.ForeignKey(related_name='domain_followup', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='domain',
            field=models.ForeignKey(related_name='domain_notification', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationauthority',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationauthority', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='domain',
            field=models.ForeignKey(related_name='domain_notificationtemplate', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
