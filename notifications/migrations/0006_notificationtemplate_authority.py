# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_authority_created_by'),
        ('notifications', '0005_auto_20150630_0408'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtemplate',
            name='authority',
            field=models.ForeignKey(related_name='notice_template_authority', default=0, to='accounts.Authority'),
            preserve_default=False,
        ),
    ]
