# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0024_authority_report_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('is_used', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('expired', models.DateTimeField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='authority',
            name='parent',
        ),
        migrations.AddField(
            model_name='authority',
            name='inherit_report_types',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='authority',
            name='inherits',
            field=models.ManyToManyField(related_name='inherits_rel_+', null=True, to='accounts.Authority', blank=True),
            preserve_default=True,
        ),
    ]
