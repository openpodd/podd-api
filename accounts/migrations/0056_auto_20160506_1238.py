# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_auto_20160125_0705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authority',
            name='domain',
            field=models.ForeignKey(related_name='domain_authority', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authorityinvite',
            name='domain',
            field=models.ForeignKey(related_name='domain_authorityinvite', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domain',
            field=models.ForeignKey(related_name='domain_user', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domains',
            field=models.ManyToManyField(related_name='multi_domain_user', verbose_name=b'Allowed in domains', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domain',
            field=models.ForeignKey(related_name='domain_userdevice', verbose_name=b'Current domain', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domains',
            field=models.ManyToManyField(related_name='multi_domain_userdevice', verbose_name=b'Allowed in domains', to='common.Domain'),
            preserve_default=True,
        ),
    ]
