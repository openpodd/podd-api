from django.contrib import admin
from notifications.models import LineMessageGroupCtrl, NotificationTemplate, NotificationAuthority


class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('description', )
    search_fields = ('description',)


class NotificationAuthorityAdmin(admin.ModelAdmin):
    search_fields = ['template__description', 'authority__name']
    list_display = ('template', 'authority', )


class LineMessageGroupCtrlAdmin(admin.ModelAdmin):
    list_display = ('authority', 'start_date', 'end_date',)

    def get_queryset(self, request):
        return super(admin.ModelAdmin, self).get_queryset(request).filter(authority__domain_id=request.user.domain_id)


# Register your models here.
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(NotificationAuthority, NotificationAuthorityAdmin)
admin.site.register(LineMessageGroupCtrl, LineMessageGroupCtrlAdmin)
