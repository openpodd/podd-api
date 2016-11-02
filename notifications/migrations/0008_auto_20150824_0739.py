# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")
    db_alias = schema_editor.connection.alias

    for nt in NotificationTemplate.objects.using(db_alias).all():
        if nt.reporter_feedback:
            nt.type = 2
        else:
            nt.type = 1

        nt.save()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_auto_20150729_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtemplate',
            name='type',
            field=models.IntegerField(default=1, max_length=2, choices=[(1, b'Report'), (2, b'Reporter Feedback'), (3, b'Notify Follow Up'), (4, b'Late Follow Up')]),
            preserve_default=True,
        ),
        migrations.RunPython(
            forwards_func,
        ),

    ]
