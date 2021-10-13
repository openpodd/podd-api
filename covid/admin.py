from django.contrib import admin

from covid.models import MonitoringReport, AuthorityInfo, DailySummary, DailySummaryByVillage


@admin.register(MonitoringReport)
class MonitoringReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'authority', 'reporter', 'name')
    raw_id_fields = ('authority', 'report', 'reporter')


@admin.register(AuthorityInfo)
class AuthorityInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'authority')
    raw_id_fields = ('authority',)


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'authority', 'date')
    raw_id_fields = ('authority', )


@admin.register(DailySummaryByVillage)
class DailySummaryByVillageAdmin(admin.ModelAdmin):
    list_display = ('id', 'authority', 'date', 'village_no')
    raw_id_fields = ('authority', )