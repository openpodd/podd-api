# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0075_authority_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorityInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('population', models.IntegerField(null=True, blank=True)),
                ('population_male', models.IntegerField(null=True, blank=True)),
                ('population_female', models.IntegerField(null=True, blank=True)),
                ('population_elder', models.IntegerField(null=True, blank=True)),
                ('num_households', models.IntegerField(null=True, blank=True)),
                ('num_villages', models.IntegerField(null=True, blank=True)),
                ('num_dogs', models.IntegerField(null=True, blank=True)),
                ('num_cats', models.IntegerField(null=True, blank=True)),
                ('year', models.IntegerField(null=True, blank=True)),
                ('authority', models.ForeignKey(related_name='authority_info_authority', to='accounts.Authority')),
            ],
            options={
            },
            bases=(models.Model,),
        ),        
    ]
