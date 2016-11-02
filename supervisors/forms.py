# -*- encoding: utf-8 -*-


from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
from django.core.exceptions import ValidationError

from accounts.models import User, Authority
from common.functions import upload_to_s3
from logs.models import LogItem
from reports.models import AdministrationArea, ReportInvestigation, ReportLaboratoryCase, Report


class SupervisorsUserForm(forms.ModelForm):
    first_name = forms.CharField(required=True, label=u'ชื่อ', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, label=u'นามสกุล', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'contact', 'telephone',
            'project_mobile_number', 'serial_number', 'running_number', 'note', 'status')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.Textarea(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'project_mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'running_number': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'email': u'อีเมล',
        }

    def save(self, commit=True, *args, **kwargs):
        instance = super(SupervisorsUserForm, self).save(commit=False)
        created_by = kwargs.pop('created_by', None)
        if created_by and instance.pk:
            for field in instance._important_fields:
                user = User.objects.get(pk=instance.pk)
                old = getattr(user, field)
                new = getattr(instance, field)
                if old != new:
                    LogItem.objects.log_action(key='USER_EDIT', created_by=created_by,
                        object1=user, data={
                            'field': field,
                            'old': old,
                            'new': new,
                        })

        if commit:
            instance.save()
        return instance



class SupervisorsAuthorityForm(forms.ModelForm):
    name = forms.CharField(required=True, label=u'ชื่อ', widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=True, label=u'รายละเอียด', widget=forms.Textarea(attrs={'class': 'form-control'}))

    # users = forms.ModelMultipleChoiceField(label=u'ผู้ใช้',
    #     queryset=User.objects.order_by('administration_area'), required=False,
    #     widget=forms.SelectMultiple(attrs={'rows':'1', 'class': 'form-control'}))
    # administration_areas = forms.ModelMultipleChoiceField(label='พื้นที',
    #     queryset=AdministrationArea.objects.all(), required=False,
    #     widget=forms.SelectMultiple(attrs={'rows':'2', 'class': 'form-control'}))
    #report_types = forms.ModelMultipleChoiceField(label='report types', queryset=ReportType.objects.all(), required=False, widget=FilteredSelectMultiple("Report Type", False, attrs={'rows':'1'}))

    class Meta:
        model = Authority
        fields = ('name', 'description')


class SupervisorsReportInvestigationForm(forms.Form):
    BOOLEAN_CHOICES = (('1', u'ใช่'), ('0', u'ไม่เป็นโรคระบาด'))

    report = forms.CharField(required=True, label=u'เลขที่รายงาน', widget=forms.TextInput(attrs={'class': 'form-control'}))
    note = forms.CharField(required=False, label=u'รายละเอียด', widget=forms.Textarea(attrs={'class': 'form-control'}))

    investigation_date = forms.DateField(label=u'วันที่ลงสืบสวนโรค', input_formats= ['%d/%m/%Y', '%Y-%m-%d'], widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker'}))
    result = forms.ChoiceField(required=True, label=u'เป็นโรคระบาดหรือไม่?', choices = BOOLEAN_CHOICES, widget=forms.RadioSelect())

    file = forms.FileField(required=False, label=u'แนบไฟล์', widget=forms.FileInput(attrs={'class': 'form-control'}))

    def clean_report(self):
        report_id = self.cleaned_data['report']
        try:
            report = Report.objects.get(id=report_id, negative=True, test_flag=False, type__in=[2])
        except Report.DoesNotExist:
            raise ValidationError("Report already exists or type not match sick/death animal.")
        return report

    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            if file.size <= settings.MAX_ATTACH_FILE_COMMENT_SIZE:
                file.seek(0)
                file_url = upload_to_s3(file)
                if not file_url:
                    raise ValidationError("Cannot upload to S3.")
                file = file_url
            else:
                raise ValidationError("Your file is too large.")
        return file


class SupervisorsReportLaboratoryCaseForm(forms.ModelForm):
    report = forms.CharField(required=True, label=u'เลขที่รายงาน', widget=forms.TextInput(attrs={'class': 'form-control'}))

    case_no = forms.CharField(required=True, label=u'เลขที่ตัวอย่าง', widget=forms.TextInput(attrs={'class': 'form-control'}))
    note = forms.CharField(required=True, label=u'รายละเอียดตัวอย่าง (เจ้าของ, ที่อยู่)', widget=forms.Textarea(attrs={'class': 'form-control'}))

    class Meta:
        model = ReportLaboratoryCase
        fields = ('report', 'case_no', 'note', 'created_by', 'updated_by')

    def clean_report(self):
        report_id = self.cleaned_data['report']
        try:
            report = Report.objects.get(id=report_id, negative=True, test_flag=False, type__in=[2])
        except Report.DoesNotExist:
            raise ValidationError("Report already exists or type not match sick/death animal.")
        return report

