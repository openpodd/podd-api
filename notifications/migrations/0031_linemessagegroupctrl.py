# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0077_auto_20240104_0548'),
        ('notifications', '0030_linemessagegroupstat'),
    ]

    operations = [
        migrations.CreateModel(
            name='LineMessageGroupCtrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('authority', models.ForeignKey(related_name='line_message_group_ctrl_authority', to='accounts.Authority')),
            ],
            options={
            },
            bases=(models.Model,),
        ),

        migrations.RunSQL("create index idx_line_message_group_ctrl_authority on notifications_linemessagegroupctrl (authority_id);"),
    ]
