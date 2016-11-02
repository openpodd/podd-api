# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0044_auto_20151002_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authority',
            name='domain',
            field=models.ForeignKey(related_name='domain_authority', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authorityinvite',
            name='domain',
            field=models.ForeignKey(related_name='domain_authorityinvite', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domain',
            field=models.ForeignKey(related_name='domain_user', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domains',
            field=models.ManyToManyField(related_name='multi_domain_user', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domain',
            field=models.ForeignKey(related_name='domain_userdevice', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domains',
            field=models.ManyToManyField(related_name='multi_domain_userdevice', to='common.Domain'),
            preserve_default=True,
        ),
    ]
