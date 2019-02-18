from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import AdminPasswordChangeForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.core.validators import validate_integer, MinLengthValidator

from accounts.models import User, GroupReportType, GroupAdministrationArea, Configuration, Authority, GroupInvite, \
    AuthorityInvite
from common.constants import (GROUP_WORKING_TYPE_CHOICES, GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_REPORT_TYPE, GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE,
    GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE)
from common.functions import publish_into_rabbitmq
from logs.models import LogItem
from reports.models import ReportType, AdministrationArea


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput, validators=[validate_integer, MinLengthValidator(4)])

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        user = super(UserCreateForm, self).save(commit=False, *args, **kwargs)

        password = self.cleaned_data['password']
        user.set_password(password)
        if user.status:
            user.display_password = password

        # REMOVE CHECK COMMIT FOR USING USER OBJECT FOR LOGGINGS
        user.save()
        LogItem.objects.log_action(key='USER_CREATE', created_by=self.created_by, object1=user)
        return user


class UserForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        instance = super(UserForm, self).save(commit=False)
        if self.created_by and instance.pk:
            for field in instance._important_fields:
                user = User.objects.get(pk=instance.pk)
                old = getattr(user, field)
                new = getattr(instance, field)
                if old != new:
                    LogItem.objects.log_action(key='USER_EDIT', created_by=self.created_by,
                        object1=user, data={
                            'field': field,
                            'old': old,
                            'new': new,
                        })

        if commit:
            instance.save()
        return instance




class UserSetPasswordForm(AdminPasswordChangeForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, validators=[validate_integer, MinLengthValidator(4)])
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, validators=[validate_integer, MinLengthValidator(4)])

    def save(self, commit=True):
        user = super(UserSetPasswordForm, self).save(commit=False)

        password = self.cleaned_data['password1']
        if user.status:
            user.display_password = password
        if commit:
            user.save()
        return user


class GroupForm(forms.ModelForm):
    name = forms.CharField(label='name', widget=forms.TextInput())
    type = forms.ChoiceField(label='type', choices=GROUP_WORKING_TYPE_CHOICES, widget=forms.Select())
    administration_areas = forms.ModelMultipleChoiceField(label='administration areas', queryset=AdministrationArea.objects.all(), required=False, widget=FilteredSelectMultiple("Administration Area", False, attrs={'rows':'2'}))
    report_types = forms.ModelMultipleChoiceField(label='report types', queryset=ReportType.objects.all(), required=False, widget=FilteredSelectMultiple("Report Type", False, attrs={'rows':'1'}))
  
    class Meta:
        model = Group
        fields = ('name', 'type')

    class Media:
        js = ('js/jquery.min.js', 'js/choose-group-type.js', )

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        if self.instance.id is not None:
            group = Group.objects.get(id=self.instance.id)
            self.fields['report_types'].initial = ReportType.objects.filter(groupreporttype__group=group)
            self.fields['administration_areas'].initial = AdministrationArea.objects.filter(groupadministrationarea__group=group)

    def save(self, commit=True):      
        group = super(GroupForm, self).save(commit=False)
        group.save()

        type = int(self.cleaned_data['type'])
        GroupReportType.objects.filter(group=group).delete()
        GroupAdministrationArea.objects.filter(group=group).delete()

        if type == GROUP_WORKING_TYPE_ADMINSTRATION_AREA:
            if self.cleaned_data['administration_areas']:
                administration_areas = self.cleaned_data['administration_areas']
                for administration_area in administration_areas:
                    group_administer_area = GroupAdministrationArea.objects.create(
                                            group = group,
                                            administration_area = administration_area,
                                        )
        elif type == GROUP_WORKING_TYPE_REPORT_TYPE:
            if self.cleaned_data['report_types']:
                report_types = self.cleaned_data['report_types']
                for report_type in report_types:
                    group_report_type = GroupReportType.objects.create(
                                            group = group,
                                            report_type = report_type,
                                        )
        elif type in [GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA]:
            if self.cleaned_data['administration_areas']:
                administration_areas = self.cleaned_data['administration_areas']
                for administration_area in administration_areas:
                    group_administer_area = GroupAdministrationArea.objects.create(
                                            group = group,
                                            administration_area = administration_area,
                                        )
        elif type in [GROUP_WORKING_TYPE_ALERT_REPORT_REPORT_TYPE, GROUP_WORKING_TYPE_ALERT_CASE_REPORT_TYPE]:
            if self.cleaned_data['report_types']:
                report_types = self.cleaned_data['report_types']
                for report_type in report_types:
                    group_report_type = GroupReportType.objects.create(
                                            group = group,
                                            report_type = report_type,
                                        )

        return group


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs = {
            'class': 'form-control',
            'placeholder': self.fields['username'].label,
            'required': 'required',
            'autofocus': 'autofocus',
        }
        self.fields['password'].widget.attrs = {
            'class': 'form-control',
            'placeholder': self.fields['password'].label,
            'required': 'required',
        }


class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = Configuration

    def save(self, force_insert=False, force_update=False, commit=True):
        config = super(ConfigurationForm, self).save(commit=False)
        if commit:
            config.save()

        publish_into_rabbitmq(exchange='configurations', exchange_type='direct',
                routing_key='update_configuration', data={})

        return config


class AuthorityForm(forms.ModelForm):

    class Meta:
        model = Authority
        widgets = {
            'users': FilteredSelectMultiple("User", False, attrs={'rows':'1'}),
            'administration_areas': FilteredSelectMultiple("AdministrationArea", False, attrs={'rows':'1'})
        }


class AuthorityInviteForm(forms.ModelForm):
    class Meta:
        model = AuthorityInvite


class GroupInviteForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(label='groups', queryset=Group.objects.all(), required=False, widget=FilteredSelectMultiple("Group", False, attrs={'rows':'1'}))

    class Meta:
        model = GroupInvite
        fields = ('name', 'groups')

    def __init__(self, *args, **kwargs):
        super(GroupInviteForm, self).__init__(*args, **kwargs)
        self.fields['groups'].choices = [(group.id, u'%s: %s' % (group.get_type_display(), group.name)) for group in self.fields['groups'].choices.queryset]

