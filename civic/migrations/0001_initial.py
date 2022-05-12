# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0075_authority_active'),
        ('common', '0009_domain_is_test'),
    ]

    operations = [
        migrations.CreateModel(
            name='LetterFieldConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=30)),
                ('header_address1', models.CharField(max_length=255)),
                ('header_address2', models.CharField(max_length=255)),
                ('sign_name', models.CharField(max_length=300)),
                ('sign_position1', models.CharField(max_length=300)),
                ('sign_position2', models.CharField(max_length=300)),
                ('footer_contact_line1', models.CharField(max_length=300)),
                ('footer_contact_line2', models.CharField(max_length=300)),
                ('footer_contact_line3', models.CharField(max_length=300)),
                ('authority', models.ForeignKey(to='accounts.Authority')),
                ('domain', models.ForeignKey(related_name='domain_letterfieldconfiguration', verbose_name=b'Current domain', to='common.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
