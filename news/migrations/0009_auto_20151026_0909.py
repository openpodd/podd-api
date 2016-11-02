# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='type',
            field=models.CharField(max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'SUBSCRIBE_AUTHORITY', b'Subscribe'), (b'SUPPORT_LIKE_ME_TOO', b'Support: like and me too'), (b'SUPPORT_LIKE_COMMENT', b'Support: like and comment'), (b'SUPPORT_ME_TOO_COMMENT', b'Support: me too and comment'), (b'SUPPORT_LIKE_ME_TOO_COMMENT', b'Support: like, me too and comment'), (b'SUPPORT_LIKE', b'Support: like'), (b'SUPPORT_ME_TOO', b'Support: me too'), (b'SUPPORT_COMMENT', b'Support: comment')]),
            preserve_default=True,
        ),
    ]
