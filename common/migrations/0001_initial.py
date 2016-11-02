# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings

from django.db import models, migrations, ProgrammingError


def forwards_func(apps, schema_editor):

    defaults = settings.DEFAULT_DOMAIN.copy()
    defaults['id'] = 1
    try:
        Domain = apps.get_model("common", "Domain")
        domain, created = Domain.objects.get_or_create(id=1, defaults=defaults)
        if created:
            print '!! Create default domain: %s(%s)' % (domain.name, domain.code)

    except ProgrammingError:
        print '!! Can not create default domain, try again later with next migrate'


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=512)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),

        migrations.RunPython(
            forwards_func,
        ),
    ]
