
from django.contrib import admin

from reports.forms import DateTimeRangeForm
from reports.models import AdministrationArea


class AdministrationAreaFilter(admin.SimpleListFilter):
    title = 'Administration Area'
    parameter_name = 'administration_area'
    template = 'admin/custom_administration_area_filter.html'

    def lookups(self, request, model_admin):
        areas = AdministrationArea.objects.all()
        return [(area.id, area.name) for area in areas]

    def queryset(self, request, queryset):
        if self.value():
            area = AdministrationArea.objects.get(id=self.value())
            area_ids = list(area.get_descendants().values_list('id', flat=True))
            area_ids.append(area.id)
            return queryset.filter(administration_area__in=area_ids)
        return queryset


class DateTimeRangeFilter(admin.filters.FieldListFilter):
    template = 'admin/custom_datetime_range_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_upto = '%s__lte' % field_path
        super(DateTimeRangeFilter, self).__init__(
            field, request, params, model, model_admin, field_path)
        self.form = self.get_form(request)

    def choices(self, cl):
        return []

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_upto]

    def get_form(self, request):
        return DateTimeRangeForm(data=self.used_parameters,
                                 field_name=self.field_path)

    def queryset(self, request, queryset):
        if self.form.is_valid():
            filter_params = dict(filter(lambda x: bool(x[1]),
                                        self.form.cleaned_data.items()))
            return queryset.filter(**filter_params)
        else:
            return queryset
