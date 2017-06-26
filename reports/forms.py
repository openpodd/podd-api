import json
import plistlib

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError

from podd_form_generator.formgenerator import dump
from podd_form_generator.graffleparser import parse
from accounts.models import Authority
from reports.models import AdministrationArea, ReportType, Report, SpreadsheetResponse, ReportInvestigation, ReportLaboratoryCase, \
                           ReportState, GoogleCalendarResponse


class ReportTypeForm(forms.ModelForm):
    file = forms.FileField(required=False, help_text="If your file upload success. Form definition is replaced by this file.")
    form_definition = forms.CharField(required=False, widget=forms.Textarea())

    class Meta:
        model = ReportType
        fields = ('name', 'code', 'category', 'authority', 'user_status', 'form_definition', 'file', 'template', 'django_template', 'summary_template', 'report_pre_save', 'report_post_save', 'weight', 'followable', 'is_system', 'follow_days', 'version')

    def clean_form_definition(self):
        if self.cleaned_data['form_definition']:
            form_definition = self.cleaned_data['form_definition']
            try:
                form_definition_data = json.loads(form_definition) 
            except:
                raise forms.ValidationError("Invalid data in form definition")
    
        return self.cleaned_data['form_definition']

    def clean_file(self):
        if self.cleaned_data['file']:
            try:
                file_form_definition = self.cleaned_data['file']
                json_file_form_definition = plistlib.readPlist(file_form_definition)
                report_definition_json = dump(parse(json_file_form_definition))
                self.cleaned_data['form_definition'] = report_definition_json
            except:
                raise forms.ValidationError("Invalid parse data to form definition in file")

        return self.cleaned_data['file']
        

class ReportForm(forms.ModelForm):

    class Meta:
        model = Report
        
    def clean_created_by(self):
        type = self.cleaned_data['type']
        administration_area = self.cleaned_data['administration_area']
        created_by = self.cleaned_data['created_by']
        # if not ((has_permission_on_report_type(user=created_by, report_type=type) and \
        #     has_permission_on_administration_area(user=created_by, administration_area=administration_area)) or \
        #     created_by.is_staff):
        #     raise forms.ValidationError("The user cannot create this report")
        return self.cleaned_data['created_by']


class DateTimeRangeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.field_name = kwargs.pop('field_name')
        super(DateTimeRangeForm, self).__init__(*args, **kwargs)
        self.fields['%s__gte' % self.field_name] = forms.DateTimeField(
                                label='Start Datetime',
                                required=False)
        self.fields['%s__lte' % self.field_name] = forms.DateTimeField(
                                label='End Datetime',
                                required=False)


class SpreadsheetResponseForm(forms.ModelForm):
    key = forms.CharField(widget=forms.Textarea())
    report_types = forms.ModelMultipleChoiceField(label='report types', queryset=ReportType.objects.all(), required=False, widget=FilteredSelectMultiple("ReportType", False, attrs={'rows':'1'}))
    # administration_areas = forms.ModelMultipleChoiceField(label='administration areas', queryset=AdministrationArea.objects.all(), required=False, widget=FilteredSelectMultiple("AdministrationArea", False, attrs={'rows':'1'}))
    authorities = forms.ModelMultipleChoiceField(label='authorities', queryset=Authority.objects.all(), required=False, widget=FilteredSelectMultiple("Authorities", False, attrs={'rows':'1'}))

    class Meta:
        model = SpreadsheetResponse


class GoogleCalendarResponseForm(forms.ModelForm):
    calendar_id = forms.CharField(widget=forms.Textarea())
    report_states = forms.ModelMultipleChoiceField(label='report states', queryset=ReportState.objects.all(), required=False, widget=FilteredSelectMultiple("ReportState", False, attrs={'rows':'1'}))
    authorities = forms.ModelMultipleChoiceField(label='authorities', queryset=Authority.objects.all(), required=False, widget=FilteredSelectMultiple("Authorities", False, attrs={'rows':'1'}))

    class Meta:
        model = GoogleCalendarResponse


class ReportInvestigationForm(forms.ModelForm):
    report = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = ReportInvestigation

    def clean_report(self):
        report_id = self.cleaned_data['report']
        try:
            report = Report.objects.get(id=report_id, negative=True, test_flag=False, type__in=[2])
        except Report.DoesNotExist:
            raise ValidationError("Report already exists or type not match sick/death animal")
        return report


class ReportLaboratoryCaseForm(forms.ModelForm):
    report = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = ReportLaboratoryCase