from django.contrib import admin
from notifications.models import NotificationTemplate, NotificationAuthority


class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('description', )
    search_fields = ('description',)

class NotificationAuthorityAdmin(admin.ModelAdmin):
    search_fields = ['template__description', 'authority__name']
    list_display = ('template', 'authority', )


# Register your models here.
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(NotificationAuthority, NotificationAuthorityAdmin)