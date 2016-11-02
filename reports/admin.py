from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from treebeard.forms import movenodeform_factory
from treebeard.admin import TreeAdmin

from reports.filters import AdministrationAreaFilter, DateTimeRangeFilter
from reports.forms import ReportTypeForm, ReportForm, SpreadsheetResponseForm, ReportInvestigationForm, ReportLaboratoryCaseForm, \
                          GoogleCalendarResponseForm
from reports.models import AdministrationArea, ReportType, Report, ReportState, CaseDefinition, SpreadsheetResponse, \
    ReportTypeCategory, ReportInvestigation, ReportLaboratoryCase, AnimalLaboratoryCause, ReportLaboratoryItem, GoogleCalendarResponse


class AdministrationAreaAdmin(LeafletGeoAdmin, TreeAdmin):
    form = movenodeform_factory(AdministrationArea)
    list_display = ('name', 'code')
    search_fields = ('name', 'code', )


class ReportAdmin(LeafletGeoAdmin):
    form = ReportForm
    change_form_template = 'admin/reports/extras/report_change_form.html'

    list_display = ('__unicode__', 'test_flag', 'type', 'administration_area', 'date')
    list_filter = ('negative', AdministrationAreaFilter, 'test_flag', 'type', ('date', DateTimeRangeFilter))
    exclude = ('parent', 'tags')


class ReportTypeCategoryAdmin(admin.ModelAdmin):
    pass


class ReportTypeAdmin(admin.ModelAdmin):
    form = ReportTypeForm


class ReportStateAdmin(admin.ModelAdmin):
    pass


class CaseDefinitionAdmin(admin.ModelAdmin):
    pass


class SpreadsheetResponseAdmin(admin.ModelAdmin):
    form = SpreadsheetResponseForm


class ReportInvestigationAdmin(admin.ModelAdmin):
    form = ReportInvestigationForm


class ReportLaboratoryCaseAdmin(admin.ModelAdmin):
    form = ReportLaboratoryCaseForm


class GoogleCalendarResponseAdmin(admin.ModelAdmin):
    form = GoogleCalendarResponseForm


admin.site.register(AdministrationArea, AdministrationAreaAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportTypeCategory, ReportTypeCategoryAdmin)
admin.site.register(ReportType, ReportTypeAdmin)
admin.site.register(ReportState, ReportStateAdmin)
admin.site.register(CaseDefinition, CaseDefinitionAdmin)
admin.site.register(SpreadsheetResponse, SpreadsheetResponseAdmin)


admin.site.register(ReportInvestigation, ReportInvestigationAdmin)
admin.site.register(ReportLaboratoryCase, ReportLaboratoryCaseAdmin)
admin.site.register(AnimalLaboratoryCause)
admin.site.register(ReportLaboratoryItem)
admin.site.register(GoogleCalendarResponse, GoogleCalendarResponseAdmin)
