# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_domain_default_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('condition', models.TextField()),
                ('domain', models.ForeignKey(related_name='domain_plan', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
