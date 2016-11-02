# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0018_notification_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='created_by',
            field=models.ForeignKey(related_name='notification_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(default=b'NEWS', max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'SUBSCRIBE_AUTHORITY', b'Subscribe'), (b'SUPPORT_LIKE_ME_TOO', b'Support: like and me too'), (b'SUPPORT_LIKE_COMMENT', b'Support: like and comment'), (b'SUPPORT_ME_TOO_COMMENT', b'Support: me too and comment'), (b'SUPPORT_LIKE_ME_TOO_COMMENT', b'Support: like, me too and comment'), (b'SUPPORT_LIKE', b'Support: like'), (b'SUPPORT_ME_TOO', b'Support: me too'), (b'SUPPORT_COMMENT', b'Support: comment')]),
            preserve_default=True,
        ),
    ]
