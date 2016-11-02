
from django.contrib import admin

from logs.models import LogAction


@admin.register(LogAction)
class LogActionAdmin(admin.ModelAdmin):
    pass
