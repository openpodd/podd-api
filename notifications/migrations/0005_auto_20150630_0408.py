# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_authority'),
        ('notifications', '0004_notification_anonymous_send'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='subscribe_authority',
            field=models.ForeignKey(related_name='subscribe_authority_notice', blank=True, to='accounts.Authority', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(default=b'NEWS', max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'SUBSCRIBE_AUTHORITY', b'Subscribe')]),
            preserve_default=True,
        ),
    ]
