# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_news_domain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='domain',
            field=models.ForeignKey(related_name='domain_news', default=1, to='common.Domain'),
            preserve_default=True,
        ),
    ]
