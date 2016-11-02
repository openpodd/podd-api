# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def initial_user_status_data(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        if user.is_volunteer:
            user.status = 'VOLUNTEER'
            user.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_user_is_volunteer'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='display_password',
            field=models.CharField(default=b'', max_length=128, verbose_name='\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(default=b'', max_length=100, verbose_name='\u0e2a\u0e16\u0e32\u0e19\u0e30\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49', choices=[(b'', b''), (b'VOLUNTEER', '\u0e2d\u0e32\u0e2a\u0e32\u0e2a\u0e21\u0e31\u0e04\u0e23\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23'), (b'ADDITION_VOLUNTEER', '\u0e2d\u0e32\u0e2a\u0e32\u0e2a\u0e21\u0e31\u0e04\u0e23\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e40\u0e15\u0e34\u0e21'), (b'COORDINATOR', '\u0e1c\u0e39\u0e49\u0e1b\u0e23\u0e30\u0e2a\u0e32\u0e19\u0e07\u0e32\u0e19')]),
            preserve_default=True,
        ),
        migrations.RunPython(initial_user_status_data, backwards),
    ]
