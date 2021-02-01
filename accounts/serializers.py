from crum import get_current_user
from django.forms import widgets
from rest_framework import serializers

from accounts.models import User, UserDevice, Authority, GroupInvite, AuthorityInvite, user_can_edit_basic_check, Party
from common.constants import USER_STATUS_CHOICES


class UserSerializer(serializers.ModelSerializer):
    name = serializers.Field('name')
    firstName = serializers.WritableField('first_name')
    lastName = serializers.WritableField('last_name')
    avatarUrl = serializers.WritableField('avatar_url')
    thumbnailAvatarUrl = serializers.WritableField('thumbnail_avatar_url')
    authorityAdmins = serializers.PrimaryKeyRelatedField('authority_admins', many=True, read_only=True)
    isStaff = serializers.BooleanField('is_staff')
    isSuperuser = serializers.BooleanField('is_superuser')
    isAnonymous = serializers.BooleanField('is_anonymous')
    isPublic = serializers.BooleanField('is_public')
    administrationArea = serializers.PrimaryKeyRelatedField('administration_area', required=False, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'name', 'username', 'firstName', 'lastName', 'status', 'contact', 'avatarUrl',
            'thumbnailAvatarUrl', 'authorityAdmins', 'isStaff', 'isSuperuser', 'isAnonymous', 'isPublic',
            'domain', 'administrationArea',
        )


class UserCommonSerializer(serializers.ModelSerializer):
    name = serializers.Field('name')

    username = serializers.WritableField('username', read_only=True)

    #TODO: hide sensitive fields below from user hasn't permission
    email = serializers.WritableField('email', required=False)
    telephone = serializers.WritableField('telephone', required=False)
    serialNumber = serializers.WritableField('serial_number', required=False)
    displayPassword = serializers.WritableField('display_password', required=False)

    firstName = serializers.WritableField('first_name', required=False)
    lastName = serializers.WritableField('last_name', required=False)
    avatarUrl = serializers.WritableField('avatar_url', required=False)
    thumbnailAvatarUrl = serializers.WritableField('thumbnail_avatar_url', required=False)

    sendInvitation = serializers.BooleanField('send_invitation', required=False)
    isAnonymous = serializers.BooleanField('is_anonymous', required=False)
    isPublic = serializers.BooleanField('is_public', required=False)

    report_count = serializers.Field('get_report_count')
    support_count = serializers.Field('get_support_count')
    category_count = serializers.Field('get_category_count')

    authority = serializers.Field('get_authority')
    dateJoined = serializers.WritableField('date_joined', required=False)
    isDeleted = serializers.BooleanField('is_deleted', required=False)

    class Meta:
        model = User
        fields = ('id', 'name', 'username', 'email', 'telephone', 'serialNumber', 'displayPassword', 'fbuid',
                  'firstName', 'lastName', 'status', 'contact', 'avatarUrl', 'thumbnailAvatarUrl', 'sendInvitation',
                  'isAnonymous', 'isPublic', 'authority', 'dateJoined')


class UserCommonAdminSerializer(UserCommonSerializer):
    username = serializers.WritableField('username')
    password = serializers.WritableField('password')


class UserCommonDetailSerializer(UserCommonSerializer):

    dateJoined = serializers.WritableField('date_joined', read_only=True)

    reportCount = serializers.Field('get_report_count')
    supportCount = serializers.Field('get_support_count')
    categoryCount = serializers.Field('get_category_count')

    class Meta:
        model = User
        fields = ('id', 'name', 'username', 'email', 'telephone', 'serialNumber', 'displayPassword', 'fbuid',
                  'firstName', 'lastName', 'status', 'contact', 'avatarUrl', 'thumbnailAvatarUrl', 'sendInvitation',
                  'isAnonymous', 'isPublic', 'reportCount', 'supportCount', 'categoryCount', 'dateJoined', 'isDeleted')


class UserCommonShortDetailSerializer(UserCommonSerializer):

    dateJoined = serializers.WritableField('date_joined', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'username', 'email', 'telephone', 'serialNumber', 'displayPassword', 'fbuid',
                  'firstName', 'lastName', 'status', 'contact', 'avatarUrl', 'thumbnailAvatarUrl',
                  'isAnonymous', 'isPublic', 'dateJoined')

    def transform_dateJoined(self, obj, value):
        if obj and obj.date_joined:
            return obj.date_joined.strftime('%Y-%m-%dT%H:%M:%SZ')
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    firstName = serializers.WritableField('first_name')
    lastName = serializers.WritableField('last_name')
    serialNumber = serializers.WritableField('serial_number', required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'firstName', 'lastName', 'serialNumber', 'telephone', 'email', 'status', 'domain')

    def restore_object(self, attrs, instance=None):
        '''
        call set_password on user object. Without this
        the password will be stored in plain text.
        '''

        user = super(UserRegistrationSerializer, self).restore_object(attrs, instance)
        if attrs.has_key('password'):
            user.set_password(attrs['password'])
        return user


class UserDeviceSerializer(serializers.ModelSerializer):
    androidId = serializers.WritableField('android_id', required=False)
    deviceId = serializers.WritableField('device_id')
    wifiMac = serializers.WritableField('wifi_mac', required=False)
    gcmRegId = serializers.WritableField('gcm_reg_id', required=False)
    apnsRegId = serializers.WritableField('apns_reg_id', required=False)

    class Meta:
        model = UserDevice
        fields = ('androidId', 'deviceId', 'brand', 'model', 'wifiMac', 'gcmRegId', 'apnsRegId', 'domain')


class UserListESSerializer(serializers.ModelSerializer):
    id = serializers.Field('pk')
    username = serializers.Field('username')
    firstName = serializers.Field('first_name')
    lastName = serializers.Field('last_name')
    fullName = serializers.Field('full_name')

    class Meta:
        model = User
        fields = ('id', 'username', 'firstName', 'lastName', 'fullName')

    def transform_id(self, obj, value):
        if value:
            try:
                return int(value)
            except:
                pass
        return value


class AttachCanEditSerializer(serializers.Serializer):

    def to_native(self, obj):


        ret = super(AttachCanEditSerializer, self).to_native(obj)
        request = self.context.get('request')

        ret['canEdit'] = False

        if request and request.user and request.user.id:
            user = request.user
        else:
            user = get_current_user()

        if obj and user:

            if hasattr(obj, 'user_can_edit'):
                ret['canEdit'] = obj.user_can_edit(user)
            else:
                ret['canEdit'] = user_can_edit_basic_check(user, True)

        return ret


class AuthorityListSerializer(serializers.ModelSerializer):

    code = serializers.WritableField('code')
    name = serializers.WritableField('name')
    description = serializers.WritableField('description', required=False)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', required=False, read_only=True)

    deepSubscribes = serializers.PrimaryKeyRelatedField('deep_subscribes', many=True, required=False, widget=widgets.TextInput)
    #subscribes = serializers.PrimaryKeyRelatedField('subscribes', many=True, required=False, read_only=True)
    inherits = serializers.PrimaryKeyRelatedField('inherits', many=True, required=False, widget=widgets.TextInput)

    tags = serializers.Field('tags.all')

    inviteCode = serializers.Field('invite.code')
    inviteExpiredAt = serializers.Field('invite.expired_date_at')

    class Meta:
        model = Authority
        fields = ('id', 'code', 'name', 'description', 'createdBy', 'inherits', 'deepSubscribes', 'group',
                  'inviteCode', 'inviteExpiredAt')



class AuthorityShortListSerializer(serializers.ModelSerializer):

    code = serializers.WritableField('code')
    name = serializers.WritableField('name')
    description = serializers.WritableField('description', required=False)
    createdBy = serializers.PrimaryKeyRelatedField('created_by', required=False, read_only=True)

    deepSubscribes = serializers.PrimaryKeyRelatedField('deep_subscribes', many=True, required=False)

    tags = serializers.Field('tags.all')

    parentName = serializers.Field('get_parent_name')

    class Meta:
        model = Authority
        fields = ('id', 'code', 'name', 'description', 'parentName')


class AuthorityInviteSerializer(serializers.ModelSerializer):

    code = serializers.WritableField('code')
    name = serializers.WritableField('name')

    inviteCode = serializers.Field('invite.code')
    inviteExpiredAt = serializers.Field('invite.expired_at')
    #inviteCodeByUserStatus = serializers.Field('invite_code_by_status')


    class Meta:
        model = Authority
        fields = ('id', 'code', 'name', 'description', 'inviteCode', 'inviteExpiredAt')

    def transform_inviteCode(self, obj, val):
        request = self.context.get('request')

        if request and request.user and request.user.status:
            trainer_authority = request.user.authority_users.all()
            if trainer_authority:
                trainer_authority = trainer_authority[0]
            else:
                trainer_authority = None

            return obj.get_invite(trainer_status=request.user.status, trainer_authority=trainer_authority).code
        else:
            return val


class AuthorityShortSerializer(serializers.ModelSerializer):
    code = serializers.WritableField('code')
    name = serializers.WritableField('name')
    description = serializers.WritableField('description', required=False)
    class Meta:
        model = Authority
        fields = ('id', 'code', 'name',)


class AuthoritySerializer(serializers.ModelSerializer, AttachCanEditSerializer):

    code = serializers.WritableField('code')
    name = serializers.WritableField('name')
    description = serializers.WritableField('description', required=False)

    createdBy = serializers.PrimaryKeyRelatedField('created_by', required=False, read_only=True)

    deepSubscribes = serializers.PrimaryKeyRelatedField('deep_subscribes', many=True, required=False, widget=widgets.TextInput)
    #subscribes = serializers.PrimaryKeyRelatedField('subscribes', many=True, required=False, read_only=True)

    users = serializers.PrimaryKeyRelatedField('users', many=True, required=False, read_only=True)
    admins = serializers.PrimaryKeyRelatedField('admins', many=True, required=False, read_only=True)
    areas = serializers.PrimaryKeyRelatedField('area_authority', many=True, required=False, widget=widgets.TextInput)
    reportTypes = serializers.PrimaryKeyRelatedField('report_types', many=True, required=False, read_only=True)
    inherits = serializers.PrimaryKeyRelatedField('inherits', many=True, required=False, widget=widgets.TextInput)
    children = serializers.PrimaryKeyRelatedField('authority_inherits', many=True, required=False, read_only=True)

    inviteCode = serializers.Field('invite.code')
    inviteExpiredAt = serializers.Field('invite.expired_at')
    #inviteCodeByUserStatus = serializers.Field('invite_code_by_status')


    tags = serializers.Field('tags.all')

    parentName = serializers.SerializerMethodField('get_parent_name')

    class Meta:
        model = Authority
        fields = ('id', 'code', 'name', 'description', 'createdBy', 'users', 'admins', 'deepSubscribes', 'areas',
                  'reportTypes', 'inherits', 'children', 'inviteCode', 'inviteExpiredAt')


class GroupInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupInvite
        fields = ('id', 'name')


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ('id', 'name')