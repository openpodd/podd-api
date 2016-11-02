# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('en_word', models.TextField()),
                ('th_word', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
