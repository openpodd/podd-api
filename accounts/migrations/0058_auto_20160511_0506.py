# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from common.constants import USER_STATUS_CHOICES


class Migration(migrations.Migration):

    def migrate_role_permissions(apps, schema_editor):
        CustomPermission = apps.get_model("accounts", "CustomPermission")
        RoleCustomPermission = apps.get_model("accounts", "RoleCustomPermission")

        # delete all CustomPermission
        CustomPermission.objects.all().delete()

        custom_permissions = ['view_dashboard_plan', 'view_dashboard_summary_report', 'view_dashboard_users']
        for custom_permission in custom_permissions:
            permission, created = CustomPermission.objects.get_or_create(name=custom_permission, codename=custom_permission)

            for status, name in USER_STATUS_CHOICES:
                if status and \
                   'VOLUNTEER' not in status:
                    RoleCustomPermission.objects.create(
                        role_custom_permissions=permission,
                        role=status
                    )

    def reverse_migrate_role_permissions(apps, schema_editor):
        pass

    dependencies = [
        ('accounts', '0057_auto_20160511_0434'),
    ]

    operations = [
        migrations.RunPython(migrate_role_permissions, reverse_migrate_role_permissions),
    ]
