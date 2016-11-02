# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0026_auto_20150619_1140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedefinition',
            name='epl',
            field=models.TextField(help_text=b'from self.code.win:time(3 day) where sickCount > 10', verbose_name='EPL from and where'),
            preserve_default=True,
        ),
    ]
