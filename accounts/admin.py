from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from common.constants import GROUP_WORKING_TYPE_CHOICES

from accounts.forms import GroupForm, UserCreateForm, UserSetPasswordForm, UserForm, ConfigurationForm, AuthorityForm, GroupInviteForm
from accounts.models import User, UserDevice, Configuration, NearbyArea, Authority, GroupInvite, CustomPermission, RoleCustomPermission


class UserAdmin(UserAdmin):
    add_fieldsets = (
        (None,
            {'fields': ('domain', 'username', 'password', 'email', 'administration_area')}
        ),
        ('Personal Info',
            {'fields': ('first_name', 'last_name', 'contact', 'telephone', 'status')}
        ),
        ('Permissions',
            {'fields': ('is_superuser', 'is_staff', 'is_active', 'groups')}
        ),
    )
    fieldsets = (
        (None,
            {'fields': ('username', 'password', 'email', 'administration_area')}
        ),
        ('Personal Info',
            {'fields': ('first_name', 'last_name', 'contact', 'telephone', 'status')}
        ),
        ('Permissions',
            {'fields': ('is_superuser', 'is_staff', 'is_active', 'groups', 'domain', 'domains')}
        ),
        ('Important dates',
            {'fields': ('date_joined', 'last_login')}
        ),
    )
    form = UserForm
    add_form = UserCreateForm
    change_password_form = UserSetPasswordForm
    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'date_joined')

    def get_form(self, request, obj=None, **kwargs):
         form = super(UserAdmin, self).get_form(request, obj, **kwargs)
         form.created_by = request.user
         return form


class GroupAdmin(admin.ModelAdmin):
    form = GroupForm
    list_display = ('name', 'group_type', )
    list_filter = ('type', )

    def group_type(self, obj):
        return "%s" % GROUP_WORKING_TYPE_CHOICES[obj.type][1]


class ConfigurationAdmin(admin.ModelAdmin):
    form = ConfigurationForm
    list_display = ('system', 'key', 'value')


class AuthorityAdmin(admin.ModelAdmin):
    form = AuthorityForm

    readonly_fields = ('report_types',)
    exclude = ('tags', )



class GroupInviteAdmin(admin.ModelAdmin):
    form = GroupInviteForm
    list_display = ('name', 'code')


class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_id')


class RoleCustomPermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'role_custom_permissions')


admin.site.register(User, UserAdmin)
admin.site.register(UserDevice, UserDeviceAdmin)

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(NearbyArea)
admin.site.register(Authority, AuthorityAdmin)

admin.site.register(GroupInvite, GroupInviteAdmin)

admin.site.register(CustomPermission)
admin.site.register(RoleCustomPermission, RoleCustomPermissionAdmin)