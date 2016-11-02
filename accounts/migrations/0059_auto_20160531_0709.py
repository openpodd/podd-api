# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from common.constants import USER_STATUS_COORDINATOR, USER_STATUS_PODD, USER_STATUS_LIVESTOCK, USER_STATUS_PUBLIC_HEALTH


SUBSCRIBE_PERMISSIONS = 'view_dashboard_summary_subscribe_report'
ADMIN_PERMISSIONS = 'view_dashboard_summary_admin_report'


class Migration(migrations.Migration):

    def migrate_role_permissions(apps, schema_editor):
        CustomPermission = apps.get_model("accounts", "CustomPermission")
        RoleCustomPermission = apps.get_model("accounts", "RoleCustomPermission")

        CustomPermission.objects.filter(codename__in=[SUBSCRIBE_PERMISSIONS, ADMIN_PERMISSIONS]).delete()

        permission, created = CustomPermission.objects.get_or_create(name=SUBSCRIBE_PERMISSIONS, codename=SUBSCRIBE_PERMISSIONS)
        for status in [USER_STATUS_PODD]:
            RoleCustomPermission.objects.create(
                role_custom_permissions=permission,
                role=status
            )

        permission, created = CustomPermission.objects.get_or_create(name=ADMIN_PERMISSIONS, codename=ADMIN_PERMISSIONS)
        for status in [USER_STATUS_COORDINATOR, USER_STATUS_LIVESTOCK, USER_STATUS_PUBLIC_HEALTH]:
            RoleCustomPermission.objects.create(
                role_custom_permissions=permission,
                role=status
            )

    def reverse_migrate_role_permissions(apps, schema_editor):
        pass

    dependencies = [
        ('accounts', '0058_auto_20160511_0506'),
    ]

    operations = [
        migrations.RunPython(migrate_role_permissions, reverse_migrate_role_permissions),
    ]
