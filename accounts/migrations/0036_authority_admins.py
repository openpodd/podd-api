# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0035_authority_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='authority',
            name='admins',
            field=models.ManyToManyField(related_name='authority_admins', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
