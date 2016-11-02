# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_authority'),
        ('notifications', '0002_auto_20150212_0400'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationAuthority',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('to', models.TextField(null=True, blank=True)),
                ('authority', models.ForeignKey(related_name='notice_authority', to='accounts.Authority')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('template', models.TextField()),
                ('condition', models.TextField()),
                ('description', models.TextField(null=True, blank=True)),
                ('reporter_feedback', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='notificationauthority',
            name='template',
            field=models.ForeignKey(related_name='notice_template', to='notifications.NotificationTemplate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notification',
            name='notification_authority',
            field=models.ForeignKey(related_name='notice_item_notice', blank=True, to='notifications.NotificationAuthority', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notification',
            name='to',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='notification',
            name='message',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='receive_user',
            field=models.ForeignKey(related_name='receive_user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='report',
            field=models.ForeignKey(blank=True, to='reports.Report', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(default=b'NEWS', max_length=100, choices=[(b'NEWS', b'News'), (b'UPDATED_REPORT_TYPE', b'Update report type'), (b'AREA', b'Area'), (b'NEARBY', b'Nearby')]),
            preserve_default=True,
        ),
    ]
