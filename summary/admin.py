from django.contrib import admin

from summary.models import AggregateReport


class AggregateReportAdmin(admin.ModelAdmin):
    pass


admin.site.register(AggregateReport, AggregateReportAdmin)
