# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0043_update_userdevice_domains'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authority',
            name='domain',
            field=models.ForeignKey(related_name='domain_authority', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authorityinvite',
            name='domain',
            field=models.ForeignKey(related_name='domain_authorityinvite', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domain',
            field=models.ForeignKey(related_name='domain_user', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='domains',
            field=models.ManyToManyField(default=1, related_name='multi_domain_user', to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domain',
            field=models.ForeignKey(related_name='domain_userdevice', default=1, to='common.Domain'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userdevice',
            name='domains',
            field=models.ManyToManyField(default=1, related_name='multi_domain_userdevice', to='common.Domain'),
            preserve_default=True,
        ),
    ]
