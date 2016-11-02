# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0029_remove_authority_inherit_report_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='created_by',
            field=models.ForeignKey(related_name='authority_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
