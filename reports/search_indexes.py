import datetime
import json
from haystack.fields import LocationField

from reports.models import Report

from haystack import indexes


class ReportIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    reportId = indexes.IntegerField(model_attr='report_id', indexed=False)
    guid = indexes.CharField(model_attr='guid', indexed=False)
    createdBy = indexes.CharField(model_attr='created_by__id')
    createdByName = indexes.CharField(model_attr='created_by__get_full_name')
    createdByThumbnailUrl = indexes.CharField(model_attr='created_by__thumbnail_avatar_url', null=True  )
    incidentDate = indexes.DateField(model_attr='incident_date')
    date = indexes.DateTimeField(model_attr='date')
    administrationArea = indexes.IntegerField(model_attr='administration_area__id')
    area = indexes.CharField(model_attr='administration_area__address')
    type = indexes.IntegerField(model_attr='type__id')
    typeName = indexes.CharField(model_attr='type__name')
    negative = indexes.BooleanField(model_attr='negative', indexed=True)
    formData = indexes.CharField(model_attr='form_data', indexed=False)
    renderedFormData = indexes.CharField(model_attr="rendered_form_data", indexed=False)
    originalFormData = indexes.CharField(model_attr='form_data', indexed=False)
    renderedOriginalFormData = indexes.CharField(model_attr="rendered_original_form_data", indexed=False)
    testFlag = indexes.BooleanField(indexed=True)
    state = indexes.IntegerField(model_attr='state__id', null=True)
    stateName = indexes.CharField(model_attr='state__name', null=True)
    stateCode = indexes.CharField(model_attr='state__code', null=True)
    parent = indexes.IntegerField(model_attr='parent__id', null=True)
    parentType = indexes.CharField(model_attr='parent_type', null=True)
    tags = indexes.MultiValueField(indexed=True, stored=True)

    #latitude = indexes.FloatField(model_attr='report_location__y', indexed=True, null=True)
    #longitude = indexes.FloatField(model_attr='report_location__x', indexed=True, null=True)
    reportLocation = LocationField(model_attr='report_location', indexed=True, null=True)
    firstImageThumbnail = indexes.CharField(null=True)
    reportTypeCategoryCode = indexes.CharField(model_attr='type__category__code', null=True)

    commentCount = indexes.IntegerField(default=0, null=True)

    domain = indexes.IntegerField(model_attr='domain__id', null=True)

    def get_model(self):
        return Report

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.select_related('administration_area', 'type', 'created_by', 'domain').filter(updated_at__lte=datetime.datetime.now())

    def prepare(self, object):
        self.prepared_data = super(ReportIndex, self).prepare(object)

        for key, val in json.loads(object.form_data).items():
            self.prepared_data[key] = val
        return self.prepared_data

    '''
    def prepare_area(self, obj):
        areas = [obj.administration_area.name]
        ancestors = obj.administration_area.get_ancestors()
        if ancestors.count() > 0:
            ancestors = ancestors.values_list('name', flat=True)
        areas.extend(ancestors)
        areas = ','.join(area for area in areas)
        return areas
    '''

    def prepare_testFlag(self, obj):
        if obj.test_flag:
            return True
        else:
            return False

    def prepare_tags(self, obj):
        return [tag.name for tag in obj.tags.all()] or None

    def prepare_firstImageThumbnail(self, obj):
        if obj.first_image_thumbnail_url:
            return obj.first_image_thumbnail_url

        if obj.images.count():
            return obj.images.all()[0].thumbnail_url
        return ''

    def prepare_commentCount(self, obj):
        return obj.comments.all().count()


