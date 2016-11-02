# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_authority_created_by'),
        ('reports', '0035_spreadsheetresponse_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrationarea',
            name='authority',
            field=models.ForeignKey(related_name='area_authority', blank=True, to='accounts.Authority', null=True),
            preserve_default=True,
        ),
    ]
