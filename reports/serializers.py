# -*- encoding: utf-8 -*-
import json
from collections import OrderedDict

from django.conf import settings
from django.contrib.gis.geos import Point
from django.forms import widgets

from rest_framework import serializers
from django.template import Template, Context

from accounts.serializers import UserSerializer, AttachCanEditSerializer
from flags.models import Flag
from common.functions import has_permission_on_report_type, has_permission_on_administration_area, filter_permitted_administration_areas_and_descendants
from logs.models import LogAction, LogItem
from plans.serializers import PlanSerializer
from reports.models import Report, ReportType, ReportImage, ReportComment, AdministrationArea, ReportState, \
    CaseDefinition, ReportTypeCategory, ReportLike, ReportMeToo, ReportAbuse, AnimalLaboratoryCause, \
    ReportLaboratoryItem, ReportAccomplishment, RecordSpec


class AdministrationAreaSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    parentName = serializers.SerializerMethodField('get_parent_name')
    isLeaf = serializers.SerializerMethodField('get_is_leaf')

    authority = serializers.PrimaryKeyRelatedField('authority', widget=widgets.TextInput)
    # tags = serializers.Field('tags.all')

    class Meta:
        model = AdministrationArea
        fields = ('id', 'name', 'parentName', 'isLeaf', 'address', 'location',
                  'code', 'authority', 'weight')
        ordering = ('weight', 'name')

    def transform_location(self, obj, value):
        if obj and obj.location:
            return json.loads(obj.location.json)
        return value

    def get_is_leaf(self, obj):
        if obj:
            try:
                return obj.is_leaf()
            except TypeError:
                return True
        return True

    def get_parent_name(self, obj):
        if obj:
            try:
                parent = obj.get_parent()
                if parent:
                    return parent.name
                else:
                    return ''
            except (TypeError, ValueError):
                return ''
        return ''


class AdministrationAreaListSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdministrationArea
        fields = ('id', 'name', 'address', 'location', 'code', 'weight')
        ordering = ('weight', 'name')

    def transform_location(self, obj, value):
        if obj and obj.location:
            return json.loads(obj.location.json)
        return value


class AdministrationAreaContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdministrationArea
        fields = ('id', 'name', 'address', 'contacts')


class AdministrationAreaDetailSerializer(AdministrationAreaSerializer):
    reportCount = serializers.Field('get_last_n_days_report_count')
    supportCount = serializers.Field('get_last_n_days_support_count')
    categoryCount = serializers.Field('get_last_n_days_category_count')
    hotReportType = serializers.Field('get_last_n_days_hot_report_types')


    class Meta:
        model = AdministrationArea
        fields = ('id', 'name', 'parentName', 'isLeaf', 'address', 'location', 'mpoly', 'code', 'authority',
                  'reportCount', 'supportCount', 'categoryCount', 'hotReportType')

    def transform_mpoly(self, obj, value):
        if obj and obj.mpoly:
            return obj.mpoly.simplify(tolerance=0.001).json
        return value


class BaseReportStateSerializer(serializers.ModelSerializer, AttachCanEditSerializer):

    reportType = serializers.PrimaryKeyRelatedField('report_type', widget=widgets.TextInput)
    name = serializers.WritableField('name')
    code = serializers.WritableField('code')
    description = serializers.WritableField('description', required=False)
    fromStates = serializers.Field('from_states')
    toStates = serializers.Field('to_states')


    class Meta:
        model = ReportState
        fields = ('id', 'reportType', 'name', 'code', 'description', 'fromStates', 'toStates')

    def transform_fromStates(self, obj, value):
        if obj and obj.id:
            return ReportStateLiteSerializer(obj.from_states, many=True).data
        else:
            return []

    def transform_toStates(self, obj, value):
        if obj and obj.id:
            return ReportStateLiteSerializer(obj.to_states, many=True).data
        else:
            return []


class ReportStateSerializer(BaseReportStateSerializer):

    allowToStates = BaseReportStateSerializer(source='allow_to_states', many=True, read_only=True)

    class Meta:
        model = ReportState
        fields = ('id', 'reportType', 'name', 'code', 'description', 'fromStates', 'toStates', 'allowToStates')


class ReportStateLiteSerializer(ReportStateSerializer):
    class Meta:
        model = ReportState
        fields = ('id', 'reportType', 'name', 'code')


class CaseDefinitionSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    reportType = serializers.PrimaryKeyRelatedField('report_type', widget=widgets.TextInput)
    fromState = serializers.PrimaryKeyRelatedField('from_state', required=False, widget=widgets.TextInput)
    toState = serializers.PrimaryKeyRelatedField('to_state', widget=widgets.TextInput)
    epl = serializers.WritableField('epl')
    code = serializers.WritableField('code')
    description = serializers.WritableField('description', required=False)
    class Meta:
        model = CaseDefinition
        fields = ('id', 'reportType', 'fromState', 'toState', 'epl', 'code', 'description')


class CaseDefinitionExplainedSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    reportType = serializers.PrimaryKeyRelatedField('report_type', widget=widgets.TextInput)
    fromState = serializers.PrimaryKeyRelatedField('from_state', required=False, widget=widgets.TextInput)
    toState = serializers.PrimaryKeyRelatedField('to_state', widget=widgets.TextInput)
    epl = serializers.WritableField('epl')
    code = serializers.WritableField('code')
    description = serializers.WritableField('description', required=False)

    class Meta:
        model = CaseDefinition
        fields = ('id', 'reportType', 'fromState', 'toState', 'epl', 'code', 'description')

    def transform_reportType(self, obj, value):
        if obj and obj.id:
            return ReportTypeListSerializer(obj.report_type).data
        else:
            return None

    def transform_fromState(self, obj, value):
        if obj and obj.id:
            return ReportStateLiteSerializer(obj.from_state).data
        else:
            return None

    def transform_toState(self, obj, value):
        if obj and obj.id:
            return ReportStateLiteSerializer(obj.to_state).data
        else:
            return None


class ReportTypeCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportTypeCategory
        fields = ('id', 'name', 'code', 'description')



class ReportTypeListSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    definition = serializers.Field(source='form_definition')
    followDays = serializers.Field(source="follow_days")
    category = serializers.PrimaryKeyRelatedField("category", many=False, read_only=True, required=False)
    categoryName = serializers.PrimaryKeyRelatedField("category", many=False, read_only=True, required=False)
    categoryCode = serializers.PrimaryKeyRelatedField("category", many=False, read_only=True, required=False)
    isFollowAction = serializers.WritableField('is_follow_action', read_only=True)

    class Meta:
        model = ReportType
        fields = ('id', 'code', 'name', 'version', 'weight', 'followable', 'followDays',
                  'category', 'categoryName', 'categoryCode', 'isFollowAction')

    def transform_followable(self, obj, value):
        if obj.followable:
            return True
        else:
            return False

    def transform_followDays(self, obj, value):
        if not value:
            return 0
        return value

    def transform_categoryName(self, obj, value):
        if value:
            return obj.category.name
        return value

    def transform_categoryCode(self, obj, value):
        if value:
            return obj.category.code
        return value

    def transform_isFollowAction(self, obj, value):
        if value:
            return value
        return False



class ReportTypeSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    definition = serializers.WritableField(source='form_definition')
    followDays = serializers.WritableField(source="follow_days", required=False)
    followable = serializers.WritableField(source="followable", required=False)
    version = serializers.WritableField(source="version", required=False)
    weight = serializers.WritableField(source="weight", required=False)
    category = serializers.PrimaryKeyRelatedField("category", many=False, read_only=True, required=False)
    categoryCode = serializers.SerializerMethodField('get_category_code')
    categoryName = serializers.SerializerMethodField('get_category_name')
    isFollowAction = serializers.WritableField('is_follow_action', read_only=True)
    authority = serializers.PrimaryKeyRelatedField('authority', required=False, widget=widgets.TextInput)

    reportStates = serializers.PrimaryKeyRelatedField('report_state_report_type', required=True, many=True, widget=widgets.TextInput)

    class Meta:
        model = ReportType
        fields = ('id', 'code', 'name', 'version', 'weight',
                  'followable', 'followDays', 'definition', 'template',
                  'authority', 'reportStates', 'category', 'categoryCode',
                  'categoryName', 'isFollowAction')

    def transform_definition(self, obj, value):
        if value:
            return json.loads(value)
        return value

    def transform_isFollowAction(self, obj, value):
        if value:
            return value
        return False

    def transform_followable(self, obj, value):
        if obj and obj.followable:
            return True
        else:
            return False

    def transform_followDays(self, obj, value):
        if not value:
            return 0
        return value

    def get_category_name(self, obj):
        return obj.category.name if obj.category else ''

    def get_category_code(self, obj):
        return obj.category.code if obj.category else ''



class ReportTypeCategorySerializer(serializers.ModelSerializer):

    #reportTypes = ReportTypeSerializer(source='report_type_categories', many=True)

    class Meta:
        model = ReportTypeCategory

        fields = ('id', 'code', 'name', 'description')


class ReportImageSerializer(serializers.ModelSerializer):
    imageUrl = serializers.WritableField('image_url')
    thumbnailUrl = serializers.WritableField('thumbnail_url')

    class Meta:
        model = ReportImage
        fields = ('report', 'guid', 'imageUrl', 'thumbnailUrl', 'note', 'location')

    def transform_location(self, obj, value):
        if obj.location:
            return {
                'latitude': obj.location.y,
                'longitude': obj.location.x
            }
        else:
            return {}


class ReportListSerializer(serializers.ModelSerializer):
    reportTypeId = serializers.Field('type')
    administrationAreaId = serializers.Field('administration_area')
    createdBy = serializers.Field('created_by')
    incidentDate = serializers.Field('incident_date')
    eventTypeName = serializers.Field('type')
    stateCode = serializers.Field('state.code')
    state = serializers.Field('state.id')
    tags = serializers.CharField(source='get_tags', read_only=True)

    reportLocation = serializers.Field(source='report_location')


    class Meta:
        model = Report
        fields = ('id', 'createdBy', 'date', 'incidentDate', 'eventTypeName', 'state', 'stateCode', 'tags', 'reportLocation', 'administrationAreaId')

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            return obj.created_by.get_full_name()
        return ''

    def transform_date(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_incidentDate(self, obj, value):
        if value:
            return value.isoformat()
        return value


class ReportListESLiteSerializer(serializers.ModelSerializer):

    reportId = serializers.Field('reportId')
    incidentDate = serializers.Field('incidentDate')
    reportLocation = serializers.Field('reportLocation.json')
    reportTypeId = serializers.Field('type')
    reportTypeCategoryCode = serializers.Field('type.category.code')

    formDataExplanation = serializers.Field(source='renderedFormData')
    firstImageThumbnail = serializers.CharField(source='firstImageThumbnail', read_only=True)



    class Meta:
        model = Report
        fields = ('id', 'reportId', 'guid', 'negative', 'incidentDate', 'reportTypeId', 'reportLocation',
                  'formDataExplanation', 'firstImageThumbnail')

    def transform_reportLocation(self, obj, value):
        if value:
            return json.loads(value)


class ReportListESSerializer(serializers.ModelSerializer):
    id = serializers.Field('pk')
    reportId = serializers.Field('reportId')
    reportTypeId = serializers.Field('type')
    reportTypeName = serializers.Field('typeName')
    administrationAreaId = serializers.Field('administrationArea')
    administrationAreaAddress = serializers.Field('administrationArea')
    incidentDate = serializers.Field('incidentDate')
    createdBy = serializers.Field('createdBy')
    createdByName = serializers.Field('createdByName')
    createdByThumbnailUrl = serializers.Field('createdByThumbnailUrl')
    flag = serializers.Field()
    testFlag = serializers.Field(source='testFlag')
    stateName = serializers.Field('stateName')
    stateCode = serializers.Field('stateCode')
    state = serializers.Field('state')
    parent = serializers.Field('parent')
    parentType = serializers.Field('parentType')
    formDataExplanation = serializers.Field(source='renderedFormData')
    renderedOriginalFormData = serializers.Field(source='renderedOriginalFormData')
    firstImageThumbnail = serializers.CharField(source='firstImageThumbnail', read_only=True)
    tags = serializers.Field('tags')

    reportLocation = serializers.CharField(source='reportLocation')
    commentCount = serializers.IntegerField(source='commentCount')

    class Meta:
        model = Report
        fields = ('id', 'reportId', 'guid', 'reportTypeId', 'reportTypeName', 'date',
            'administrationAreaId', 'negative', 'incidentDate', 'createdBy', 'createdByName', 'createdByThumbnailUrl', 'flag', 'testFlag',
            'formDataExplanation', 'renderedOriginalFormData', 'administrationAreaAddress', 'firstImageThumbnail',
            'state', 'stateCode', 'stateName', 'parent', 'parentType', 'tags', 'reportLocation', 'commentCount')

    def transform_testFlag(self, obj, value):
        if value:
            return True
        else:
            return False

    def transform_reportTypeName(self, obj, value):
        if obj.testFlag:
            return u'ทดสอบ' + value
        else:
            return value

    def transform_id(self, obj, value):
        if value:
            try:
                return int(value)
            except:
                pass
        return value

    def transform_flag(self, obj, value):
        return ''

    def transform_date(self, obj, value):
        if value:
            from django.utils import timezone
            value = value.replace(tzinfo=timezone.utc)
            return value
        return value

    def transform_administrationAreaAddress(self, obj, value):
        if obj and obj.area:
           return obj.area
        return value

    def transform_commentCount(self, obj, value):
        return value if value else 0

    '''
    def transform_firstImageThumbnail(self, obj, value):
        if value:
            try:
                report = Report.objects.get(pk=value)
                if len(report.images.all()):
                    return report.images.all()[0].thumbnail_url
                return ''
            except Report.DoesNotExist:
                return ''
        return value

    def transform_reportLocation(self, obj, value):
        if value:
            try:
                report = Report.objects.get(pk=value)
                if report.report_location:
                    return json.loads(report.report_location.json)
                else:
                    return ''
            except Report.DoesNotExist:
                return ''
        return value
    '''


class PositiveReportListESSerializer(ReportListESSerializer):
     class Meta:
        model = Report
        fields = ('id', 'reportId', 'guid', 'reportTypeId', 'reportTypeName', 'date',
            'administrationAreaId', 'negative', 'incidentDate', 'createdBy', 'createdByName', 'flag', 'testFlag',
            'formDataExplanation', 'renderedOriginalFormData', 'administrationAreaAddress', 'firstImageThumbnail',
            'state', 'stateCode', 'stateName', 'parent', 'tags', 'reportLocation')

     def transform_date(self, obj, value):
        if obj and obj.date:
           return obj.date.strftime('%Y-%m-%dT%H:%M:%SZ')
        return ''

     def transform_incidentDate(self, obj, value):
        if obj and obj.incidentDate:
           return obj.incidentDate.strftime('%Y-%m-%d')
        return ''


class ReportListESWFormDataSerializer(ReportListESSerializer):
    formData = serializers.Field('formData')
    originalFormData = serializers.Field('original_form_data')

    class Meta:
        model = Report
        fields = ('id', 'reportId', 'guid', 'reportTypeId', 'reportTypeName', 'date',
            'administrationAreaId', 'negative', 'incidentDate', 'createdBy', 'createdByName',
            'flag', 'formData', 'originalFormData', 'testFlag', 'stateCode', 'state', 'parent', 'tags', 'reportLocation')

    def transform_formData(self, obj, value):
        if value:
            return json.loads(value)
        return value


class ReportListFullSerializer(ReportListESWFormDataSerializer):
    authority = serializers.SerializerMethodField('get_authority')
    createdByStatus = serializers.SerializerMethodField('get_created_by_status')

    class Meta:
        model = Report
        fields = ('id', 'reportId', 'guid', 'reportTypeId', 'reportTypeName', 'date',
            'administrationAreaId', 'negative', 'incidentDate', 'createdBy', 'createdByName',
            'flag', 'formData', 'originalFormData', 'testFlag', 'stateCode', 'state', 'parent',
            'tags', 'reportLocation', 'authority', 'createdByStatus')

    def get_authority(self, obj):
        if obj and obj.administrationArea:
            try:
                administration_area = AdministrationArea.objects.get(id=obj.administrationArea)
                authority = administration_area.authority
                if authority:
                    return {'id': authority.id, 'name': authority.name}
                else:
                    return None
            except AdministrationArea.DoesNotExist:
                return None
        return None

    def get_created_by_status(self, obj):
        from accounts.models import User
        if obj and obj.createdBy:
            try:
                created_by = User.objects.get(id=obj.createdBy)
                return created_by.status if created_by else None
            except User.DoesNotExist:
                return None
        return None


class ReportSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    reportId = serializers.WritableField('report_id')
    reportTypeId = serializers.PrimaryKeyRelatedField('type', widget=widgets.TextInput)
    reportTypeName = serializers.Field('type.name')
    reportTypeCode = serializers.Field('type.code')
    reportTypeCategoryCode = serializers.Field('type.category.code')

    isStateChanged = serializers.BooleanField('state_changed', read_only=True)
    stateCode = serializers.Field('state.code')
    stateName = serializers.Field('state.name')
    stateId = serializers.Field('state.id')

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    incidentDate = serializers.WritableField('incident_date')
    administrationAreaId = serializers.PrimaryKeyRelatedField('administration_area', required=False, widget=widgets.TextInput)
    administrationAreaAddress = serializers.CharField(source='administration_area.id', read_only=True)
    administrationAreaName = serializers.CharField(source='administration_area.name', read_only=True)

    formData = serializers.WritableField('form_data', required=False)
    originalFormData = serializers.Field('original_form_data')
    reportLocation = serializers.WritableField('report_location', required=False)
    reportLocationString = serializers.WritableField('report_location', required=False, read_only=True)
    images = ReportImageSerializer(many=True, read_only=True)
    firstImageThumbnail = serializers.CharField(source='pk', read_only=True)

    createdByObject = serializers.PrimaryKeyRelatedField('created_by', many=False, read_only=True)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', many=False, read_only=True)
    createdById = serializers.PrimaryKeyRelatedField('created_by', many=False, read_only=True)
    createdByName = serializers.PrimaryKeyRelatedField('created_by', many=False, read_only=True)
    createdByThumbnailUrl = serializers.Field(source='created_by.thumbnail_avatar_url')
    createdByContact = serializers.Field(source='created_by.contact')
    createdByTelephone = serializers.Field(source='created_by.telephone')
    createdByProjectMobileNumber = serializers.Field(source='created_by.project_mobile_number')

    testFlag = serializers.BooleanField('test_flag', required=False)
    formDataExplanation = serializers.Field(source='rendered_form_data')
    renderedOriginalFormData = serializers.Field(source='rendered_original_form_data')
    parentGuid = serializers.Field('parent.guid')
    tags = serializers.Field('tags.all')

    isPublic = serializers.WritableField('is_public', read_only=True)
    isAnonymous = serializers.WritableField('is_anonymous', required=False)
    isCurated = serializers.BooleanField('is_curated', read_only=True)

    parent = serializers.PrimaryKeyRelatedField('parent', required=False, widget=widgets.TextInput)
    parentType = serializers.Field('parent_type')

    likeCount = serializers.Field(source='like_count')
    commentCount = serializers.Field(source='comment_count')
    meTooCount = serializers.Field(source='me_too_count')

    likeId = serializers.Field(source='get_like.id')
    meTooId = serializers.Field(source='get_me_too.id')

    boundary = serializers.Field(source='boundary')


    class Meta:
        model = Report
        fields = (
            'id', 'reportId', 'guid', 'reportTypeId', 'reportTypeName', 'reportTypeCode', 'reportTypeCategoryCode',
            'isStateChanged', 'stateCode', 'stateName', 'stateId', 'date', 'createdAt', 'isAnonymous', 'createdByObject',
            'incidentDate', 'createdBy', 'createdById', 'createdByName', 'administrationAreaId', 'formData', 'originalFormData', 'negative', 'testFlag',
            'createdByTelephone', 'createdByProjectMobileNumber', 'createdByThumbnailUrl',
            'parent', 'parentType', 'reportLocation', 'reportLocationString', 'remark', 'images', 'firstImageThumbnail', 'createdByContact',
            'administrationAreaAddress', 'administrationAreaName', 'formDataExplanation', 'renderedOriginalFormData', 'parentGuid', 'tags', 'isPublic',
            'likeCount', 'commentCount', 'meTooCount', 'likeId', 'meTooId', 'boundary', 'isCurated',
        )

    # General transformations.
    def transform_reportTypeCategoryCode(self, obj, value):
        if value:
            return value
        else:
            return ''

    def transform_isStateChanged(self, obj, value):
        if value:
            return True
        else:
            return False

    def transform_testFlag(self, obj, value):
        if value:
            return True
        else:
            return False

    def transform_reportTypeName(self, obj, value):
        if obj.test_flag:
            return u'ทดสอบ' + value
        else:
            return value

    def transform_firstImageThumbnail(self, obj, value):
        if value:
            try:
                report = Report.objects.get(pk=value)
                if report.first_image_thumbnail_url:
                    return report.first_image_thumbnail_url

                if len(report.images.all()):
                    return report.images.all()[0].thumbnail_url
                return ''
            except Report.DoesNotExist:
                return ''
        return value

    def transform_commentCount(self, obj, value):
        return obj.comments.filter(created_by__is_public=True, state__isnull=True).count()


    def validate_administrationAreaId(self, attrs, source):
        value = attrs[source]
        user = self.context.get('request').user

        if not value and not user.is_public:
            if attrs['negative']:
                raise serializers.ValidationError('This field is required.')
            elif not user.administration_area:

                ## find group of administration_area
                # TODO: Fix from client
                administration_areas = filter_permitted_administration_areas_and_descendants(user)
                if administration_areas.count() >= 1:
                    attrs[source] = administration_areas[0]
                else:
                    raise serializers.ValidationError('This user does not have default admintration area.')
            else:
                attrs[source] = user.administration_area

        if not settings.DISABLE_CHECK_REPORT_ADMIN_AREA_PERMISSION:
            if value and not has_permission_on_administration_area(user=user, administration_area=value):
                raise serializers.ValidationError('You do not have permission to create report in this area.')
        return attrs

    def validate_reportLocation(self, attrs, source):
        if attrs.has_key(source):
            value = attrs[source]
            if not isinstance(value, dict) or not value.has_key('longitude') or not value.has_key('latitude'):
                raise serializers.ValidationError('Invalid format.')

            if value.has_key('longitude') and value['longitude'] > 180 or value['longitude'] < -180:
                raise serializers.ValidationError('Longitude must be in between -180 to 180 degree.')

            if value.has_key('latitude') and value['latitude'] > 90 or value['latitude'] < -90:
                raise serializers.ValidationError('Latitude must be in between -90 to 90 degree.')

            attrs[source] = 'POINT (%s %s)' % (value['longitude'], value['latitude'])
        return attrs

    def transform_formData(self, obj, value):
        if value:
            return json.loads(value)
        return value

    def transform_originalFormData(self, obj, value):
        if value:
            return json.loads(value)
        return value

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_date(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_incidentDate(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_reportLocation(self, obj, value):
        if obj and obj.report_location:
            return json.loads(obj.report_location.json)
        elif obj and obj.administration_location:
            return json.loads(obj.administration_location.json)
        elif obj:
            return json.loads(obj.administration_area.locaion.json)
        else:
            return value

    def transform_reportLocationString(self, obj, value):
        if obj and obj.report_location:
            return obj.report_location.json
        elif obj and obj.administration_location:
            return obj.administration_location.json
        elif obj:
            return obj.administration_area.locaion.json
        else:
            return value

    def get_latest_flag(self, obj):
        return ''

    def transform_administrationAreaAddress(self, obj, value):
        if value:
            administrationArea = AdministrationArea.objects.get(pk=value)
            return administrationArea.address
        return value

    # Transform for anonymous reports.
    def transform_createdBy(self, obj, value):
        if obj.is_anonymous:
            return "ไม่ระบุชื่อผู้รายงาน"
        if value:
            created_by = obj.created_by
            return created_by.get_full_name() or created_by.username
        return value

    def transform_createdByObject(self, obj, value):
        if obj and obj.id:
            user = UserSerializer(obj.created_by).data
            if obj.is_anonymous:
                user = {
                    "id": 0,
                    "username": "ไม่ระบุชื่อผู้รายงาน",
                    "name": "ไม่ระบุชื่อผู้รายงาน",
                    "firstName": "",
                    "lastName": "",
                    "contact": None,
                    "avatarUrl": None,
                    "thumbnailAvatarUrl": None
                }
            return user
        return None

    def transform_createdById(self, obj, value):
        if obj.is_anonymous:
            return None
        else:
            return value

    def transform_createdByName(self, obj, value):
        return self.transform_createdBy(obj, value)

    def transform_createdByContact(self, obj, value):
        if obj.is_anonymous:
            return None
        else:
            return value


    def transform_administrationAreaAddress(self, obj, value):
        if value:
            try:
                administrationArea = AdministrationArea.objects.get(pk=value)
            except AdministrationArea.DoesNotExist:
                return ''

            return administrationArea.address
        return value

    def transform_createdByThumbnailUrl(self, obj, value):
        if obj.is_anonymous:
            return None
        else:
            return value

    def transform_createdByTelephone(self, obj, value):
        if obj.is_anonymous:
            return None
        else:
            return value

    def transform_createdByProjectMobileNumber(self, obj, value):
        if obj.is_anonymous:
            return None
        else:
            return value


class ReportCommentSerializer(serializers.ModelSerializer, AttachCanEditSerializer):
    reportId = serializers.PrimaryKeyRelatedField('report', widget=widgets.TextInput)
    fileUrl = serializers.WritableField('file_url', required=False)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)
    updatedBy = serializers.PrimaryKeyRelatedField('updated_by', read_only=True)
    updatedAt = serializers.WritableField('updated_at', read_only=True)

    class Meta:
        model = ReportComment
        fields = ('id', 'reportId', 'message', 'fileUrl', 'createdBy', 'createdAt', 'updatedBy', 'updatedAt')
        read_only_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            if obj.created_by == obj.report.created_by and obj.report.is_anonymous == True:
                return {
                    'id': 0,
                    'username': u'ไม่ระบุชื่อผู้รายงาน',
                    'name': u'ไม่ระบุชื่อผู้รายงาน',
                    'firstName': '',
                    'lastName': '',
                    'contact': None,
                    'avatarUrl': None,
                    'thumbnailAvatarUrl': None
                }
            return UserSerializer(obj.created_by).data
        return ''

    def transform_updatedBy(self, obj, value):
        if obj and obj.id:
            if obj.updated_by == obj.report.created_by and obj.report.is_anonymous == True:
                return {
                    'id': 0,
                    'username': u'ไม่ระบุชื่อผู้รายงาน',
                    'name': u'ไม่ระบุชื่อผู้รายงาน',
                    'firstName': '',
                    'lastName': '',
                    'contact': None,
                    'avatarUrl': None,
                    'thumbnailAvatarUrl': None
                }
            return UserSerializer(obj.updated_by).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_updatedAt(self, obj, value):
        if value:
            return value.isoformat()
        return value


class ReportLikeSerializer(serializers.ModelSerializer):
    reportId = serializers.PrimaryKeyRelatedField('report', widget=widgets.TextInput)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)

    class Meta:
        model = ReportLike
        fields = ('id', 'reportId', 'createdBy', 'createdAt' )
        read_only_fields = ('created_at', )

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.created_by).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value


class ReportMeTooSerializer(serializers.ModelSerializer):
    reportId = serializers.PrimaryKeyRelatedField('report', widget=widgets.TextInput)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)

    class Meta:
        model = ReportMeToo
        fields = ('id', 'reportId', 'createdBy', 'createdAt' )
        read_only_fields = ('created_at', )

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.created_by).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value


class ReportAbuseSerializer(serializers.ModelSerializer):
    reportId = serializers.PrimaryKeyRelatedField('report', widget=widgets.TextInput)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)

    class Meta:
        model = ReportAbuse
        fields = ('id', 'reportId', 'createdBy', 'createdAt', 'reason')
        read_only_fields = ('created_at', )

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.created_by).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value


class DashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=200)
    address = serializers.CharField()
    location = serializers.CharField(max_length=200)
    positive = serializers.IntegerField()
    negative = serializers.IntegerField()
    positiveCases = ReportListSerializer(many=True)
    negativeCases = ReportListSerializer(many=True)

    def transform_location(self, obj, value):
        if obj and obj.location:

            if type(obj.location) is Point:
                return json.loads(obj.location.json)
            else:
                return json.loads(obj.location)
        return value


class AnimalLaboratoryCauseSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnimalLaboratoryCause
        fields = ('id', 'name')


class ReportLaboratoryItemSerializer(serializers.ModelSerializer):
    sampleNo = serializers.WritableField('sample_no')
    positiveCauses = serializers.PrimaryKeyRelatedField('positive_causes', many=True, required=False)
    negativeCauses = serializers.PrimaryKeyRelatedField('negative_causes', many=True, required=False)

    positiveCausesText = serializers.Field('positive_causes_text')
    negativeCausesText = serializers.Field('negative_causes_text')

    class Meta:
        model = ReportLaboratoryItem
        fields = ('id', 'case', 'sampleNo', 'positiveCauses', 'negativeCauses', 'note',
                  'positiveCausesText', 'negativeCausesText')


class ReportAccomplishmentSerializer(serializers.ModelSerializer):
    reportId = serializers.PrimaryKeyRelatedField('report', widget=widgets.TextInput)
    publicShowcase = serializers.WritableField('public_showcase')
    createdBy = serializers.PrimaryKeyRelatedField('created_by', read_only=True)
    createdAt = serializers.WritableField('created_at', read_only=True)
    updatedBy = serializers.PrimaryKeyRelatedField('updated_by', read_only=True)
    updatedAt = serializers.WritableField('updated_at', read_only=True)

    class Meta:
        model = ReportAccomplishment
        fields = ('id', 'reportId', 'title', 'description', 'createdBy', 'createdAt', 'updatedBy', 'updatedAt',
                  'publicShowcase',)
        read_only_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

    def transform_createdBy(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.created_by).data
        return ''

    def transform_updatedBy(self, obj, value):
        if obj and obj.id:
            return UserSerializer(obj.updated_by).data
        return ''

    def transform_createdAt(self, obj, value):
        if value:
            return value.isoformat()
        return value

    def transform_updatedAt(self, obj, value):
        if value:
            return value.isoformat()
        return value


class RecordSpecSerializer(serializers.ModelSerializer):
    tplHeader = serializers.WritableField('tpl_header', read_only=True)
    tplSubHeader = serializers.WritableField('tpl_subheader', read_only=True)
    parentId = serializers.PrimaryKeyRelatedField('parent', read_only=True)
    timestamp = serializers.WritableField('updated_at', read_only=True)
    typeId = serializers.PrimaryKeyRelatedField('type', read_only=True)
    groupKey = serializers.WritableField('group_key', read_only=True)

    class Meta:
        model = RecordSpec
        fields = ('id', 'timestamp', 'parentId', 'tplHeader', 'tplSubHeader', 'name', 'typeId', 'groupKey')

    def transform_timestamp(self, obj, value):
        if value:
            return int(obj.updated_at.strftime('%s'))
        return value

    def transform_parentId(self, obj, value):
        if value:
            return value
        return 0

    def transform_groupKey(self, recordSpec, value):
        user = self.context['request'].user
        if value == RecordSpec.GROUP_KEY_ALL:
            return "all"
        elif value == RecordSpec.GROUP_KEY_USER:
            return user.username.replace('.', '_')
        elif value == RecordSpec.GROUP_KEY_AUTHORITY:
            authority = user.authority_users.all()[0]
            return str(authority.id)
        return "all"


class RecordSpecListSerializer(serializers.ModelSerializer):
    timestamp = serializers.WritableField('updated_at', read_only=True)

    class Meta:
        model = RecordSpec
        fields = ('id', 'timestamp', 'name', 'type')

    def transform_timestamp(self, obj, value):
        if value:
            return int(obj.updated_at.strftime('%s'))
        return value


class MyReportSerializer(serializers.ModelSerializer):
    """
    display 
    - authority name
    - report type name
    - topic (extract from form data)
    - date    
    """
    id = serializers.Field('id')
    date = serializers.Field('date')
    authorityName = serializers.SerializerMethodField('get_authority')
    reportTypeName = serializers.Field('type.name')
    topic = serializers.SerializerMethodField('get_topic')
    image = serializers.SerializerMethodField('get_first_image')

    class Meta:
        model = Report
        fields = ('id', 'date', 'authorityName', 'reportTypeName', 'topic', 'image',)
        
    def get_authority(self, obj):
        if obj and obj.administration_area and obj.administration_area.authority:
            return obj.administration_area.authority.name
        return None

    def get_topic(self, obj):
        if obj and obj.form_data:
            form_data = json.loads(obj.form_data)
            if form_data and form_data.has_key('topic'):
                return form_data['topic']
            return obj.rendered_form_data
            
        return None
    
    def get_first_image(self, obj):
        if not obj.images and obj.images.count() == 0:
            return None
        image = obj.images.first()
        if not image:
            return None
        return image.thumbnail_url
    

class MyReportDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field('id')
    date = serializers.Field('date')
    authorityName = serializers.SerializerMethodField('get_authority')
    reportTypeName = serializers.Field('type.name')
    topic = serializers.SerializerMethodField('get_topic')
    description = serializers.Field('rendered_form_data')
    status = serializers.Field('state.name')
    colorStatus = serializers.SerializerMethodField('get_color_status')
    finishedDate = serializers.SerializerMethodField('get_finished_date')
    finishedImage = serializers.SerializerMethodField('get_finished_image')

    class Meta:
        model = Report
        fields = ('id', 'date', 'authorityName', 'reportTypeName', 'topic', 'description', 'status', 'colorStatus', 'finishedDate', 'finishedImage')
        
    def get_authority(self, obj):
        if obj and obj.administration_area and obj.administration_area.authority:
            return obj.administration_area.authority.name
        return None
    
    def get_topic(self, obj):
        if obj and obj.form_data:
            form_data = json.loads(obj.form_data)
            if form_data and form_data.has_key('topic'):
                return form_data['topic']
            return obj.rendered_form_data
            
        return None
    
    color_mapping = {
        '1085ca98-c3ad-11e4-b': { # สัตว์ป่วยตาย
            u'รายงาน': "grey",
            'Report': "grey",
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'ยังไม่สงสัยเหตุระบาด': 'green',
            'Insignificant Report': 'green',
            u'สงสัยเหตุระบาด': 'yellow',
            'Suspect Outbreak': 'yellow',
            u'ไม่ใช่เหตุระบาด': 'green',
            'No Outbreak Identified': 'green',
            'Unsuspected Outbreak': 'green',
            u'เหตุระบาด': 'red',
            'Outbreak': 'red',
            u'ควบคุมเหตุเสร็จสิ้นแล้ว': 'green',
            'Finish': 'green',
            u'สงสัยว่าเป็นโรคพิษสุนัขบ้า': 'yellow',            
            u'สันนิษฐานว่าเป็นโรคพิษสุนัขบ้า': 'red',
            u'ยืนยันว่าเป็นโรคพิษสุนัขบ้า': 'red',
            u'ไม่ใช่โรคพิษสุนัขบ้า': 'green',
        },
        '108546a4-c3ad-11e4-b': { # สัตว์กัด
            u"รายงาน": "grey",
            "Report": "grey",
            u"เหตุผิดปกติ": "yellow",
            "Case": "yellow",
            u"ยังไม่สงสัยเหตุระบาด": "green",
            "No Outbreak Identified": "green",
            u"สงสัยเหตุระบาด": "red",
            "Suspect Outbreak": "red",
            u"ไม่ใช่เหตุระบาด": "green",
            "False Report": "green",
            u"เหตุระบาด": "red",
            "Outbreak": "red",
        },
        '10868f6e-c3ad-11e4-b': { # อาหารปลอดภัย
            u'รายงาน': 'grey',
            'Report': 'grey',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'red',
            'Complete Case': 'red',
            u'ดำเนินการเสร็จสิ้น': 'green',
            'Finish': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
            'Insignificant': 'green',
        },
        '10873e00-c3ad-11e4-b': { # คุ้มครองผู้บริโภค
            u'รายงาน': 'grey',
            'Report': 'grey',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'red',
            'Complete Case': 'yellow',
            u'ดำเนินการเสร็จสิ้น': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
            'Finish': 'green',
        },
        '10865da0-c3ad-11e4-b': { # สิ่งแวดล้อม
            u'รายงาน': 'grey',
            'Report': 'grey',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'ควบคุมเหตุเสร็จสิ้นแล้ว': 'green',
            u'ดำเนินการเสร็จสิ้น': 'green',
            'Finish': 'green',
            u'ยังไม่สงสัยเหตุระบาด': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
            'Insignificant': 'green',
            'Complete Case': 'yellow',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'yellow',
        },
        'natural-disaster': { # ภัยธรรมชาติ
            u'รายงาน': 'grey',
            'Report': 'grey',            
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'yellow',            
            u'ดำเนินการเสร็จสิ้น': 'green',
            'Finish': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
        },
        'publichazard': { # สาธารณภัย
            u'รายงาน': 'grey',
            'Report': 'grey',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'yellow',
            'Complete Case': 'yellow',
            u'ดำเนินการเสร็จสิ้น': 'green',
            'Finish': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'False Report': 'green',
        },
        '1084f56e-c3ad-11e4-b': { #โรคในคน
            u'รายงาน': 'grey',
            'Report': 'grey',
            u'เหตุผิดปกติ': 'red',
            'Case': 'red',
            u'กำลังดำเนินการผ่านระบบ สธ.': 'red',
            u'กำลังดำเนินการผ่าน สธ.': 'red',
            u'ดำเนินการเสร็จสิ้น': 'green',
            u'ควบคุมเสร็จสิ้น': 'green',
            'Finish': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
            'Insignificant': 'green',
            'False Report': 'green',
            u'สรุปไม่ได้': 'yellow',
        },
        'civic': {
            u'รายงาน': 'red',
            u'กำลังดำเนินการผ่านหน่วยงาน': 'yellow',
            u'ประสานหน่วยงานที่เกี่ยวข้อง': 'blue',
            u'ดำเนินการเสร็จสิ้น': 'green',
            u'ไม่ใช่เหตุผิดปกติ': 'green',
        }
    }
    
    def get_color_status(self, obj):
        report_type_code = obj.type.code
        if report_type_code in self.color_mapping:
            status = obj.state.name
            if status in self.color_mapping[report_type_code]:
                return self.color_mapping[report_type_code].get(status, 'none')
        return 'none'
        

    def get_finished_date(self, obj):
        log_action = LogAction.objects.get(name='REPORT_STATE_CHANGE')
        history_queryset = LogItem.objects.filter(action=log_action, object_id1=obj.id).order_by('-created_at')

        finished_date = None
        for log_item in history_queryset:
            state = ReportState.default_manager.get(id=log_item.object_id2, domain_id=obj.domain_id)
            if state.code == 'finish':
                finished_date = log_item.created_at

        return finished_date

    def get_finished_image(self, obj):
        for comment in obj.comments.order_by('-created_at'):
            if comment.file_url and comment.message.find(u'ผล') > -1:
                return comment.file_url
        return None