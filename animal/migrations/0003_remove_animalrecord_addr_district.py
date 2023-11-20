# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('animal', '0002_animalrecord_vaccine_other'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='animalrecord',
            name='addr_district',
        ),
    ]
