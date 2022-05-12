from django.contrib import admin

from civic.models import LetterFieldConfiguration


class LetterFieldConfigurationAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('code',)


admin.site.register(LetterFieldConfiguration, LetterFieldConfigurationAdmin)
