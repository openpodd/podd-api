# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_remove_domain_domain'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0060_auto_20151015_0446'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportLike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportlike', to='common.Domain')),
                ('report', models.ForeignKey(related_name='likes', to='reports.Report')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportMeToo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('domain', models.ForeignKey(related_name='domain_reportmetoo', to='common.Domain')),
                ('report', models.ForeignKey(related_name='me_toos', to='reports.Report')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reportmetoo',
            unique_together=set([('report', 'created_by')]),
        ),
        migrations.AlterUniqueTogether(
            name='reportlike',
            unique_together=set([('report', 'created_by')]),
        ),
        migrations.AddField(
            model_name='report',
            name='comment_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='like_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='me_too_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
