# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_custom_permission_data(apps, schema_editor):
    CustomPermission = apps.get_model('accounts', 'CustomPermission')
    CustomPermission.objects.get_or_create(
        name='View Dashboard Summary Report', codename='view_dashboard_summary_report')
    CustomPermission.objects.get_or_create(
        name='View Dashboard Summary Inactive Users',
        codename='view_dashboard_summary_inactive_users')
    CustomPermission.objects.get_or_create(
        name='View Dashboard Visualization', codename='view_dashboard_visualization')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_auto_20150209_0855'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('codename', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'ordering': ('codename',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='user',
            name='user_custom_permissions',
            field=models.ManyToManyField(to='accounts.CustomPermission', verbose_name='Custom Permissions', blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(initial_custom_permission_data, backwards),
    ]
