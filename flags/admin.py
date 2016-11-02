from django.contrib import admin

from common.models import Domain


class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')


admin.site.register(Domain, DomainAdmin)

