# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_user_telephone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='value',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
