# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0032_migrate_data_unsubscribes_inherits'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorityInvite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expired_at', models.DateTimeField()),
                ('authority', models.ForeignKey(related_name='authority_invite_authority', to='accounts.Authority')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
