# -*- coding: utf-8 -*-

import datetime
import json
import operator
import random
import uuid

import facebook
import os
import xlwt
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q, Count
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from haystack.query import SearchQuerySet
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes, link
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from rest_framework.response import Response

from accounts import tasks
from accounts.models import Configuration, UserDevice, User, Authority, UserCode, AuthorityInvite
from accounts.pub_tasks import publish_user_profile
from accounts.serializers import (UserDeviceSerializer, UserListESSerializer, UserSerializer,
                                  AuthoritySerializer, UserRegistrationSerializer, UserCommonSerializer,
                                  AuthorityListSerializer, AuthorityShortListSerializer,
                                  UserCommonDetailSerializer, AuthorityInviteSerializer, UserCommonAdminSerializer)
from common.constants import (USER_STATUS_PODD, USER_STATUS_LIVESTOCK, USER_STATUS_PUBLIC_HEALTH, USER_STATUS_VOLUNTEER,
                              USER_STATUS_ADDITION_VOLUNTEER,
                              USER_STATUS_CHOICES)
from common.functions import (filter_permitted_administration_areas_and_descendants,
                              upload_to_s3, resize_and_crop, publish_gcm_message, generate_username,
                              get_public_authority, publish_apns_message, filter_permitted_report_types,
                              filter_permitted_users, filter_permitted_authority,
                              filter_permitted_users_for_authorities_admin)
from common.models import Domain, get_current_domain_id
from common.serializers import DomainSerializer
from firebase.functions import create_token
from logs.models import LogItem
from notifications.models import Notification
from reports.models import ReportType, AdministrationArea
from reports.serializers import ReportTypeSerializer, AdministrationAreaListSerializer
from summary.functions import summary_by_show_user_detail


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def configuration(request):

    try:
        device = UserDevice.objects.get(user=request.user)
    except UserDevice.DoesNotExist:
        device = UserDevice(
            user=request.user
        )

    data = request.DATA.copy()
    data['domain'] = request.user.domain.id
    serializer = UserDeviceSerializer(device, data=data)

    if serializer.is_valid():
        serializer.save()

        report_type_queryset = ReportType.objects.filter(id__in=filter_permitted_report_types(request.user), is_system=False, id__gt=0)
        if not request.user.is_staff and request.user.status:
            report_type_queryset = report_type_queryset.filter(Q(user_status='') | Q(user_status__icontains=(request.user.status)))

        area_queryset = filter_permitted_administration_areas_and_descendants(request.user)

        context = {
            'fullName': request.user.get_full_name(),
            'administrationAreas': AdministrationAreaListSerializer(area_queryset, many=True).data,
            'reportTypes': ReportTypeSerializer(report_type_queryset, many=True).data,
            'domains': DomainSerializer(request.user.domains.all(), many=True).data,
            'domain': DomainSerializer(request.user.domain).data
        }

        configurations = Configuration.objects.filter(system='android.configuration')
        for config in configurations:
            context[config.key] = config.value

        return Response(context)

    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def users_search(request):
    queryset = SearchQuerySet().models(User)
    limit = request.REQUEST.get('limit', 10)

    queryset = queryset.filter(domain=get_current_domain_id(request.user))

    username = request.REQUEST.get('username', '')
    if username:
        queryset = queryset.filter(username__startswith=username)

    query = request.REQUEST.get('query', u'')
    if query:
        queryset = queryset.filter()
        queryset = queryset.raw_search(u'text:*%s*' % (query, ))

    queryset = queryset.order_by('username')[:limit]

    serializer = UserListESSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def gcm_registration(request):
    if hasattr(request.user, 'device'):
        device = request.user.device
    else:
        return Response({'detail': 'This user does not register this device.'},
            status=status.HTTP_400_BAD_REQUEST)

    gcm = request.DATA.get('gcmRegId', '')
    
    if gcm:
        try:
            gcm_device = UserDevice.objects.filter(gcm_reg_id=gcm)
        except UserDevice.DoesNotExist:
            pass
        else:
            gcm_device.delete()

        device.gcm_reg_id = gcm
        device.save()

        ######### SEND GCM MESSAGE #########
        try:
            welcome_message = Configuration.objects.get(system='android.server.push_notification', key='welcome_message').value
        except Configuration.DoesNotExist:
            pass
        else:
            message_type = 'news'
            publish_gcm_message([device.gcm_reg_id], welcome_message, message_type)
            publish_apns_message([device.apns_reg_id], welcome_message)
    else:
        return Response({'gcmRegId': 'This field is required.'},
            status=status.HTTP_400_BAD_REQUEST)

    return Response()


# http://stackoverflow.com/questions/14567586/token-authentication-for-restful-api-should-the-token-be-periodically-changed
class ObtainNewAuthToken(ObtainAuthToken):
    # serializer_class = EmailAuthTokenSerialzer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.object['user']

            if user.is_deleted:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)

            user_data = UserSerializer(user).data
            user_data.update({
                'token': token.key,
                'permissions': user.get_all_custom_permissions(),
            })
            return Response(user_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


obtain_auth_token = ObtainNewAuthToken.as_view()


class CanEditModel(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return self.has_permission(request, view)

        if hasattr(obj, 'user_can_edit'):
            return obj.user_can_edit(request.user)


class AuthorityViewSet(viewsets.ModelViewSet):
    model = Authority
    serializer_class = AuthoritySerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (CanEditModel, )

    def get_queryset(self):
        return Authority.objects.all().prefetch_related('inherits', 'deep_subscribes').select_related('created_by')

    def list(self, request):
        queryset = self.get_queryset().annotate(num_inherits=Count('inherits')).order_by('num_inherits', 'id')

        # Done: --> TODO: filter only allowed authorities
        if not request.user.is_staff:
            subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'
            authority_ids = filter_permitted_authority(request.user, subscribes=subscribes)
            queryset = queryset.filter(id__in=authority_ids)

        if request.QUERY_PARAMS.get('manage') and not request.user.is_staff:
            queryset = queryset.filter(Q(admins=request.user) | Q(created_by=request.user))

        if request.QUERY_PARAMS.get('self') and not request.user.is_staff:
            queryset = queryset.filter(Q(users=request.user))

        if request.QUERY_PARAMS.get('mine'):
            queryset = queryset.filter(Q(users=request.user))

        if request.QUERY_PARAMS.get('page_size'):
            queryset = queryset[:request.QUERY_PARAMS.get('page_size')]

        if request.QUERY_PARAMS.get('short'):
            serializer = AuthorityShortListSerializer(queryset, many=True, context={'request': request})
        elif request.QUERY_PARAMS.get('invite'):
            serializer = AuthorityInviteSerializer(queryset, many=True, context={'request': request})
        else:
            serializer = AuthorityListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.get_queryset().prefetch_related('report_types', 'authority_inherits', 'administration_areas', 'admins', 'users')
        return super(AuthorityViewSet, self).retrieve(request, *args, **kwargs)

    def pre_save(self, obj):
        if not obj.id and self.request.DATA.get('createByParent'):
            obj.created_by = self.request.user

    def post_save(self, obj, created=False):
        from cacheops import invalidate_model
        invalidate_model(AdministrationArea)

        if created:
            obj.users.add(self.request.user)

    @link()
    def get_authorities_unavailable_for_subscribe(self, request, pk=None):
        authority = self.get_object()
        inherits = authority.get_inherits_all()
        children = authority.get_children_all()

        if len(inherits):
            inherits = inherits[1:]

        unavailable_for_subscribe = set(inherits) | set(children)


        queryset = self.get_queryset()
        queryset = queryset.filter(id__in=unavailable_for_subscribe)

        serializer = AuthorityListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @link()
    def get_authorities_available_for_subscribe(self, request, pk=None):
        authority = self.get_object()
        inherits = authority.get_inherits_all()
        children = authority.get_children_all()

        if len(inherits):
            inherits = inherits[1:]

        available_for_subscribe = set(inherits) | set(children)

        queryset = self.get_queryset()
        queryset = queryset.exclude(id__in=available_for_subscribe)

        serializer = AuthorityListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action()
    def renew_invitation_code(self, request, pk=None):
        authority = self.get_object()
        authority.renew_invite()
        serializer = AuthorityListSerializer(authority, context={'request': request})
        return Response(serializer.data)

    @action()
    def tags(self, request, pk=None):
        if request.DATA.get('tags') or request.DATA.get('tags') == []:
            authority = self.get_object()
            old_tags = list(authority.tags.all().values_list('name', flat=True))
            try:
                authority.tags.clear()
                for tag in request.DATA.get('tags'):
                    authority.tags.add(tag['text'])
                
            except KeyError:
                authority.tags.clear()
                for tag in old_tags:
                    authority.tags.add(tag)

        return Response({})

    @action(methods=['post', 'delete'])
    def users(self, request, pk=None):
        authority = self.get_object()

        if not request.user.is_staff and authority.admins.filter(id=request.user.id).count() == 0:
            return Response({'success': False}, status.HTTP_401_UNAUTHORIZED)

        user_id = request.DATA.get('userId') or request.DATA.get('id')
        user = User.objects.get(id=user_id)

        is_delete = request.DATA.get('delete') or request.method == 'DELETE'

        if not is_delete:
            authority.users.add(user)
        else:
            authority.users.remove(user)
        return Response({'success': True})

    @action(methods=['post', 'delete'])
    def admins(self, request, pk=None):
        authority = self.get_object()

        if not request.user.is_staff and authority.admins.filter(id=request.user.id).count() == 0:
            return Response({'success': False}, status.HTTP_401_UNAUTHORIZED)

        user_id = request.DATA.get('userId') or request.DATA.get('id')
        user = User.objects.get(id=user_id)

        is_delete = request.DATA.get('delete') or request.method == 'DELETE'

        if not is_delete:
            authority.admins.add(user)
        else:
            authority.admins.remove(user)

        return Response({'success': True})


class UserViewSet(viewsets.ModelViewSet):
    model = User
    serializer_class = UserCommonAdminSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (CanEditModel, )

    def list(self, request):
        queryset = self.get_queryset().filter(is_deleted=False).order_by('id')
        subscribes = request.QUERY_PARAMS.get('subscribe') == 'true'
        if not request.user.is_staff:
            user_ids = filter_permitted_users(request.user, subscribes=subscribes)
            queryset = queryset.filter(id__in=user_ids)

        is_volunteer = request.QUERY_PARAMS.get('isVolunteer')
        if is_volunteer:
            queryset = queryset.filter(status__in=[USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER])

        order = request.QUERY_PARAMS.get('order')
        if order:
            queryset = queryset.order_by(order)
        else:
            queryset = queryset.order_by('username')

        # username
        query = request.QUERY_PARAMS.get('query')
        if query:
            query_words = query.split(' ')

            q1 = [Q(first_name__icontains=word) for word in query_words]
            q2 = [Q(last_name__icontains=word) for word in query_words]
            q3 = [Q(username__icontains=word) for word in query_words]
            q4 = [Q(email__icontains=word) for word in query_words]

            merged_q = q1 + q2 + q3 + q4

            queryset = queryset.filter(reduce(operator.or_, merged_q))

        if request.QUERY_PARAMS.get('page_size'):

            page = int(request.QUERY_PARAMS.get('page', None) or 0)
            page_size = int(request.QUERY_PARAMS.get('page_size', None) or 20)

            if request.QUERY_PARAMS.get('page'):
                page = page * page_size
                page_size = page + page_size

            queryset = queryset[page:page_size]

        serializer = UserCommonSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        user = get_object_or_404(queryset, pk=pk)

        serializer = UserCommonDetailSerializer(user)
        return Response(serializer.data)

    def update(self, request, pk=None):
        data = request.DATA.copy()
        password = data.get('password')
        if password and password.strip() != '':
            queryset = self.get_queryset()
            user = get_object_or_404(queryset, pk=pk)

            password = password.strip()
            user.set_password(password)
            user.display_password = password
            user.save()

        return super(UserViewSet, self).update(request, pk)

    def create(self, validated_data):
        data = validated_data.DATA.copy()

        now = timezone.now()
        pass_time = now - datetime.timedelta(minutes=5)

        if data.get('serialNumber'):
            try:
                user = User.objects.filter(serial_number=data['serialNumber'], date_joined__lt=pass_time).latest('id')
                if user:
                    return Response({'detail': 'serialNumber already exist.', 'serialNumber': ['Serial number is not found.']},
                        status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                pass

        if not data.get('username'):
           data['username'] = str(uuid.uuid4())[:10].replace('-', '')

        rand = random.randint(0, 99999)
        password = '{0:05d}'.format(rand)
        data['status'] = USER_STATUS_ADDITION_VOLUNTEER
        data['password'] = password
        data['domain'] = get_current_domain_id

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.username = generate_username(user.id)
            user.display_password = password
            user.save()

            serializer = UserCommonDetailSerializer(user)
            token, created = Token.objects.get_or_create(user=user)
            serializer.data.update({
                'token': token.key,
                'permissions': user.get_all_custom_permissions(),
                'displayPassword': user.display_password,
            })

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    def destroy(self, request, pk):
        queryset = self.get_queryset()
        user = get_object_or_404(queryset, pk=pk)

        if not request.user.is_staff:
            allowed_user_ids = filter_permitted_users_for_authorities_admin(request.user)
            queryset = queryset.filter(id__in=allowed_user_ids)

        try:
            user = queryset.get(id=user.id)
            user.delete()
        except User.DoesNotExist:
            return Response({u'detail': u'You do not have permission to perform this action.'},
                     status=status.HTTP_403_FORBIDDEN)

        LogItem.objects.log_action(
            key='USER_IS_DELETED',
            created_by=request.user,
            object1=user,
            object2=request.user,
        )

        serializer = UserCommonDetailSerializer(user)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def profile_image(request, pk=None):
    url = 'http://www.cmonehealth.org/dashboard/images/avatar.6a5c9777.png'
    try:
        user = User.objects.get(pk=pk)
        if user.avatar_url:
            url = user.avatar_url
    except User.DoesNotExist:
        pass

    return redirect(url)



@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def ping(request):
    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def user_profile(request):
    can_set_flag = False
    serializer = UserCommonDetailSerializer(request.user, data=request.DATA, partial=True)
    if request.method == 'POST':
        if serializer.is_valid():
            new_user = False
            user = serializer.object
            facebook_access_token = request.DATA.get('facebookAccessToken') or request.DATA.get('facebook_access_token')
            if facebook_access_token:

                # if request.DATA.get('force'):
                #     user.is_active = False
                #     user.save()

                graph = facebook.GraphAPI(facebook_access_token)
                profile = graph.get_object('me', fields='id,name,email,picture.type(large)')
                try:
                    try:
                        exist_user = User.objects.get(fbuid=profile.get('id'))
                        if request.DATA.get('force'):
                            user = exist_user
                        elif exist_user != user:
                            return Response({"detail": "facebookAccessToken already exist"},
                                  status=status.HTTP_400_BAD_REQUEST)

                    except User.DoesNotExist:
                        email = profile.get('email') or ('%s@facebook.com' % profile['id'])
                        try:
                            exist_user = User.objects.get(is_public=True, email=email)
                            if request.DATA.get('force') or exist_user == user:
                                user = exist_user
                                user.fbuid = profile['id']
                            else:
                                return Response({"detail": "email already exist"},
                                                status=status.HTTP_400_BAD_REQUEST)

                        except User.DoesNotExist:
                            user.username = email
                            user.email = email
                            user.fbuid = profile['id']
                            user.first_name = profile['name']
                            user.avatar_url = profile['picture']['data']['url']
                            user.thumbnail_avatar_url = profile['picture']['data']['url']
                            new_user = True

                    user.is_anonymous = False

                except facebook.GraphAPIError:
                    return Response({'facebookAccessToken': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

            if request.DATA.get('email'):
                if not User.objects.filter(email=request.DATA['email']).count():
                    new_user = True

                if not request.DATA.get('force') and User.objects.exclude(id=user.id).filter(is_public=True, email=request.DATA['email']).count():
                    return Response({"detail": "email already exist"}, status=status.HTTP_400_BAD_REQUEST)

                if request.DATA.get('force'):
                    try:
                        user = User.objects.get(username=request.DATA['email'])
                    except User.DoesNotExist:
                        user.username = request.DATA['email']
                        user.email = request.DATA['email']
                else:
                    user.username = request.DATA['email']
                    user.email = request.DATA['email']

                user.is_anonymous = False

            if request.DATA.get('firstName'):
                user.first_name = request.DATA['firstName']

            if request.DATA.get('lastName'):
                user.last_name = request.DATA['lastName']

            if request.DATA.get('telephone'):
                user.telephone = request.DATA['telephone']

            user.is_active = True
            user.save()

            serializer = UserCommonDetailSerializer(user)
            token, created = Token.objects.get_or_create(user=user)
            serializer.data.update({
                'token': token.key,
                'permissions': user.get_all_custom_permissions(),
                'displayPassword': user.display_password,
            })

            if new_user:
                tasks.send_alert_register_complete.delay(serializer.object)

            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.user.is_staff == True or \
        request.user.is_superuser == True or \
        request.user.status == USER_STATUS_PODD or \
        request.user.status == USER_STATUS_LIVESTOCK or \
        request.user.status == USER_STATUS_PUBLIC_HEALTH: 
        can_set_flag = True

    serializer.data['canSetFlag'] = can_set_flag
    serializer.data['authority'] = request.user.get_authority() if not request.user.is_staff else None
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def upload_image_profile(request, pk=None):
    image = request.FILES.get('image')

    if pk:
        user = User.objects.get(pk=pk)

        if user.is_active and request.user != user and not request.user.is_staff:
            return Response({"detail": "can't modify another active user"},
                            status=status.HTTP_400_BAD_REQUEST)

    else:
        user = request.user
    
    if image:
        serializer = UserSerializer(user, data=request.DATA)
        if image.size <= settings.MAX_ATTACH_FILE_COMMENT_SIZE:
            thumbnail = default_storage.save(image.name, ContentFile(image.read()))
            image.seek(0)

            thumbnail_path = os.path.join(settings.MEDIA_ROOT, thumbnail)
            resize_and_crop(thumbnail_path, thumbnail_path, (80, 80))

            (image_name, image_ext) = os.path.splitext(image.name)
            thumbnail_file = File(open(thumbnail_path), '%s-thumbnail%s' % (image_name, image_ext))

            avatar_url = upload_to_s3(image)
            thumbnail_avatar_url = upload_to_s3(thumbnail_file)

            if avatar_url and thumbnail_avatar_url:
                serializer.object.avatar_url = avatar_url
                serializer.object.thumbnail_avatar_url = thumbnail_avatar_url
                serializer.object.save()

                now = datetime.datetime.now()
                month = '%s/%s' % (now.month, now.year)
                user_detail = json.loads(summary_by_show_user_detail(user=serializer.object, month=month))
                user_detail['username'] = serializer.object.username
                user_detail['avatarUrl'] = avatar_url
                user_detail['thumbnailAvatarUrl'] = thumbnail_avatar_url
                publish_user_profile(user_detail)

                return Response(serializer.data)
            else:
                return Response({"detail": "Cannot upload your image,"},
                    status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Cannot upload image size > 10 MB."},
                status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "image is required."},
            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def user_domains(request):

    user = request.user
    domain_id = request.GET.get('domain')

    if domain_id:
        try:
            domain = user.domains.all().get(id=domain_id)
        except Domain.DoesNotExist:
            return Response({"detail": "domain does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.domain = domain
        user.save()

    return Response({
        'domain': DomainSerializer(user.domain).data,
        'domains': DomainSerializer(user.domains.all(), many=True).data
    })


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def update_password(request):
    password = request.DATA.get('password', '')
    if len(password) < 4: 
        return Response({"password": "Invalid password. Please try again. Only Number[0-9] and length > 3 (eg. 1234)"},
            status=status.HTTP_400_BAD_REQUEST)

    try:
        int(password)
    except:
        return Response({"password": "Invalid password. Please try again. Only Number[0-9] and length > 3 (eg. 1234)"},
            status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.set_password(password)
    if user.status:
        old = user.display_password
        new = password
        LogItem.objects.log_action(key='USER_EDIT', created_by=user,
            object1=user, data={
                'field': 'password',
                'old': old,
                'new': new,
            }
        )
        user.display_password = password

    user.save()

    tasks.send_alert_change_password_complete.delay(user)
    return Response({})


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def visualization_volunteer_user(request):
    if request.QUERY_PARAMS.get('userId'):
        try:
            user = User.objects.get(id=request.QUERY_PARAMS.get('userId'))
            if not (user.status == USER_STATUS_VOLUNTEER or user.status == USER_STATUS_ADDITION_VOLUNTEER):
                return Response({"userId": "Invalid userId. userId must be volunteer."},
                        status=status.HTTP_400_BAD_REQUEST)
        except: 
            return Response({"userId": "Invalid userId. userId must be volunteer."},
                    status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"userId": "Invalid userId. userId is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    month = request.QUERY_PARAMS.get('month')
    try:
        month_start = datetime.datetime.strptime(month, '%m/%Y')
        month_end = month_start + relativedelta(months=+1, days=-1)
    except:
        return Response({"month": "Invalid month. Please try again. (eg. 1/2015)"},
                        status=status.HTTP_400_BAD_REQUEST)

    force = request.QUERY_PARAMS.get('force', False)
    user_detail = json.loads(summary_by_show_user_detail(user=user, month=month, force=force))
    return Response(user_detail)


# Configuration
@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def list_configuration(request):
    if not request.user.is_staff:
        return Response({}, status.HTTP_401_UNAUTHORIZED)

    system = request.QUERY_PARAMS.get('system')
    if system:
        configurations = Configuration.objects.filter(system=system)

        config = {}
        for configuration in configurations:
            config[configuration.key] = configuration.value

        return Response(config)
    else:
        return Response({"system": "System is required."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def list_group_structure(request):
    if not request.user.is_staff:
        return Response({}, status.HTTP_401_UNAUTHORIZED)

    groups = {}
    for group in Group.objects.all():
        users = set(group.user_set.values_list('id', flat=True))

        if not groups.has_key(group.type):
            groups[group.type] = {}

        for area in group.groupadministrationarea_set.all():
            if not groups[group.type].has_key(area.administration_area.id):
                groups[group.type][area.administration_area.id] = set()

            groups[group.type][area.administration_area.id].update(users)

        for report_type in group.groupreporttype_set.all():
            if not groups[group.type].has_key(report_type.report_type.id):
                groups[group.type][report_type.report_type.id] = set()

            groups[group.type][report_type.report_type.id].update(users)

    gen_user = {}
    for user in User.objects.filter(is_superuser=False).select_related('device'):
        gen_user[user.id] = {
            'status': user.status,
            'email': user.email,
            'project_mobile_number': user.project_mobile_number,
            'gcm_reg_id': user.device.gcm_reg_id if hasattr(user, 'device') else '',
        }

    superuser = {}
    for user in User.objects.filter(is_superuser=False).select_related('device'):
        superuser[user.id] = {
            'status': user.status,
            'email': user.email,
            'project_mobile_number': user.project_mobile_number,
            'gcm_reg_id': user.device.gcm_reg_id if hasattr(user, 'device') else '',
        }

    return Response({
        'groups': groups,
        'gen_user': gen_user,
        'superuser': superuser,
    })


@api_view(['GET'])
def get_authority_by_invitation_code(request):
    invitation_code = request.GET.get('invitationCode')

    if not invitation_code:
        return Response({"detail": "invitationCode is required.", 'invitationCode': ['Invitation code is required.']}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invite = AuthorityInvite.objects.filter(disabled=False, expired_at__gte=timezone.now(), code=invitation_code).latest('created_at')
        authority = invite.authority
    except (ValueError, AuthorityInvite.DoesNotExist):
        return Response({'detail': 'invitationCode is not found.', 'invitationCode': ['Invitation code is not found.']}, status=status.HTTP_400_BAD_REQUEST)

    serializer = AuthoritySerializer(authority)
    return Response(serializer.data)


@api_view(['GET'])
def get_group_by_invitation_code(request):
    return get_authority_by_invitation_code(request)


@api_view(['POST'])
def user_register_by_authority(request):


    data = request.DATA.copy()
    print data
    data['username'] = str(uuid.uuid4())[:10].replace('-', '')
    data['status'] = data.get('status') or USER_STATUS_ADDITION_VOLUNTEER

    rand = random.randint(0, 99999)
    password = '{0:05d}'.format(rand)
    data['password'] = password

    invitation_code = data.get('group') or data.get('authority') or data.get('code')

    if not invitation_code:
        return Response({"detail": "code is required.", 'group': ['Code is required.']},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        invite = AuthorityInvite.objects.filter(disabled=False, expired_at__gte=timezone.now(), code=invitation_code).latest('created_at')
        authority = invite.authority
        user_status = invite.status or USER_STATUS_ADDITION_VOLUNTEER
        trainer_status = invite.trainer_status or user_status
        trainer_authority_id = (invite.trainer_authority and invite.trainer_authority.id) or None

    except (ValueError, AuthorityInvite.DoesNotExist):
        return Response({'detail': 'authority is not found.', 'group': ['Authority is not found.']}, status=status.HTTP_400_BAD_REQUEST)

    data['domain'] = authority.domain.id
    serializer = UserRegistrationSerializer(data=data)

    if serializer.is_valid():
        now = timezone.now()
        pass_time = now - datetime.timedelta(minutes=5)

        try:
            user = User.objects.filter(serial_number=data['serialNumber'], date_joined__lt=pass_time).latest('id')

            if user:
                return Response(
                    {'detail': 'serialNumber already exist.', 'serialNumber': ['Serial number is not found.']},
                    status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:

            try:
                user = User.objects.filter(serial_number=data['serialNumber'], date_joined__gte=pass_time).latest('id')
            except User.DoesNotExist:
                user = None

        if not user:

            try:
                serializer.save()
            except Exception as e:
                print e

            user = serializer.object

            user.username = generate_username(user.id)
            user.display_password = password
            user.status = user_status
            user.trainer_status = trainer_status
            user.trainer_authority_id = trainer_authority_id
            user.save()

            LogItem.objects.log_action(key='USER_CREATE', created_by=user, object1=user, data={
                'invitationCode': invitation_code,
            })

        authority.users.add(user)

        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        user_data.update({
            'token': token.key,
            'permissions': user.get_all_custom_permissions(),
            'displayPassword': user.display_password,
        })

        return Response(user_data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def user_register_by_group(request):

    return user_register_by_authority(request)


@api_view(['POST'])
def user_forgot_password(request):
    email = request.DATA.get('email')
    serial_number = request.DATA.get('serialNumber')

    if not email and not serial_number:
        return Response({'detail': 'serialNumber or email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if email:
            user = User.objects.get(email=email)
        elif serial_number:
            user = User.objects.get(serial_number=serial_number)

    except User.DoesNotExist:
        return Response({'detail': 'user is not found.'}, status=status.HTTP_400_BAD_REQUEST)
    else:

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        telephone = (user.project_mobile_number or user.telephone)
        if not telephone:
            telephone = ''

        code = UserCode(user=user)
        code.save()

        if telephone:
            tasks.send_alert_forgot_password_sms.delay(user, uid=uid, token=token, code=code)

        if user.email:
            tasks.send_alert_forgot_password_email.delay(user, uid=uid, token=token, code=code)

        return Response({'uid': uid, 'token': token, 'telephone': telephone, 'email': email}, status=status.HTTP_200_OK)
    

@api_view(['POST'])
def user_code_login(request, uidb64=None, token=None):
    code = request.DATA.get('code', '')
    if not code:
        return Response({'detail': 'code is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid_int = urlsafe_base64_decode(uidb64)
        user = User.objects.get(id=uid_int)
    except (ValueError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        user_authen = authenticate(username=user.username, code=code, ignore_password=True)
        if not user_authen:
            return Response({'detail': 'code is wrong or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user_codes = UserCode.objects.filter(user=user_authen)
        user_codes.update(is_used = True)

        LogItem.objects.log_action(key='USER_LOGIN_CODE', created_by=user, object1=user)
            
        token, created = Token.objects.get_or_create(user=user_authen)
        user_data = UserSerializer(user_authen).data
        user_data.update({
            'token': token.key,
            'permissions': user_authen.get_all_custom_permissions(),
            'displayPassword': user.display_password,
        })
        
        return Response(user_data)
    else:
        return Response({'detail': 'link invalid.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def user_register_by_user_device(request, domain_id):

    data = request.DATA.copy()
    gcm_reg_id = data.get('gcmRegId', '')
    apns_reg_id = data.get('apnsRegId', '')

    # if not gcm_reg_id and not apns_reg_id:
    #     return Response({'detail': 'gcmRegId/apnsRegId is not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if gcm_reg_id and apns_reg_id:
        return Response({'detail': 'wrong device.'}, status=status.HTTP_400_BAD_REQUEST)

    authority = get_public_authority(domain_id)

    domain = authority.domain
    data['domain'] = domain.id

    serializer = UserDeviceSerializer(data=data)
    if serializer.is_valid():
        try:
            device = UserDevice.objects.get(device_id=data.get('deviceId'))
        except UserDevice.DoesNotExist:
            device = None

        if not device:
            rand = random.randint(0, 99999)
            password = '{0:05d}'.format(rand)

            try:

                user = User.objects.create(display_password=password, status=USER_STATUS_ADDITION_VOLUNTEER,
                                           is_anonymous=True, is_public=True, domain=domain)
                LogItem.objects.log_action(key='USER_CREATE', created_by=user, object1=user, data={})

                authority.users.add(user)

                serializer.object.user = user
                serializer.save()

                device = serializer.object

            except Exception as e:
                print e

            token, created = Token.objects.get_or_create(user=user)
            user_data = UserSerializer(user).data
            user_data.update({
                'token': token.key,
                'permissions': user.get_all_custom_permissions(),
                'displayPassword': user.display_password,
            })

            if device and not user.is_anonymous:
                ######### SEND GCM MESSAGE #########
                try:
                    welcome_message = Configuration.objects.get(system='android.server.push_notification', key='welcome_message').value
                except Configuration.DoesNotExist:
                    pass
                else:
                    message_type = 'news'
                    publish_gcm_message([device.gcm_reg_id], welcome_message, message_type)
                    publish_apns_message([device.apns_reg_id], welcome_message)

            return Response(user_data, status=status.HTTP_201_CREATED)

        else:
            user = device.user
            token, created = Token.objects.get_or_create(user=user)
            user_data = UserSerializer(user).data
            user_data.update({
                'token': token.key,
                'permissions': user.get_all_custom_permissions(),
                'displayPassword': user.display_password,
            })
            return Response(user_data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

'''
@api_view(['POST'])
def facebook_connect(request, domain_id):

    facebook_access_token = request.DATA.get('facebook_access_token')
    if not facebook_access_token:
        return Response({'facebook_access_token': 'facebook_access_token. This field is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        graph = facebook.GraphAPI(facebook_access_token)
        profile = graph.get_object('me', fields='id,name,email,picture.type(large)')

        try:
            user = User.objects.get(fbuid=profile.get('id'))
            serializer = UserCommonSerializer(user)
        except User.DoesNotExist:
            email = profile.get('email') or ('%s@facebook.com' % profile['id'])

            try:
                user = User.objects.get(email=email)
                user.username = email
                user.fbuid = profile['id']
                user.save()
                serializer = UserCommonSerializer(user)
            except User.DoesNotExist:

                # create new user.
                rand = random.randint(0, 99999)
                user_data = {
                    'fbuid': profile['id'],
                    'firstName': profile['name'],
                    'email': email,
                    'avatarUrl': profile['picture']['data']['url'],
                    'thumbnailAvatarUrl': profile['picture']['data']['url'],
                    'status': USER_STATUS_ADDITION_VOLUNTEER,
                    'isAnonymous': False,
                    'isPublic': True,
                    'username': email,
                    'displayPassword': '{0:05d}'.format(rand),
                    'domain': domain_id
                }

                serializer = UserCommonSerializer(data=user_data)
                if serializer.is_valid():
                    serializer.save()

                    user = serializer.object
                    LogItem.objects.log_action(key='USER_CREATE', created_by=user, object1=user, data={})

                    try:
                        authority = Authority.objects.get(code='public_%s' % domain_id, domain_id=domain_id)
                    except Authority.DoesNotExist:
                        authority = Authority.objects.create(code='public_%s' % domain_id,
                                                             name='public_%s' % domain_id,
                                                             description='public', domain_id=domain_id)

                    if authority.administration_areas.all().count() == 0:
                        AdministrationArea.objects.create(code='public_%s' % domain_id,
                                                          name='public_%s' % domain_id,
                                                          authority=authority,
                                                          location='POINT (100.552206 13.808277)',
                                                          domain_id=domain_id)

                    authority.users.add(user)

                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # TOKEN
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        user_data.update({
            'token': token.key,
            'permissions': user.get_all_custom_permissions(),
            'displayPassword': user.display_password,
        })

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except facebook.GraphAPIError:
        return Response({'facebook_access_token': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

'''


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def update_device(request):
    data = request.DATA.copy()
    gcm_reg_id = data.get('gcmRegId', '')
    apns_reg_id = data.get('apnsRegId', '')

    if gcm_reg_id and apns_reg_id:
        return Response({'detail': 'wrong device.'}, status=status.HTTP_400_BAD_REQUEST)

    data['domain'] = request.user.domain.id

    serializer = UserDeviceSerializer(data=data)

    if serializer.is_valid():

        try:
            device = UserDevice.objects.get(device_id=data.get('deviceId'))

            device.android_id = data.get('androidId', '')
            device.wifi_mac = data.get('wifiMac', '')

            device.brand = data.get('brand', '')
            device.model = data.get('model', '')

            device.gcm_reg_id = data.get('gcmRegId', '')
            device.apns_reg_id = data.get('apnsRegId', '')

            if device.user != request.user:
                if device.user.is_anonymous:
                    device.user.is_active = False
                    device.user.save()

                UserDevice.objects.filter(user=request.user).delete()
                device.user = request.user

            device.save()

            serializer = UserDeviceSerializer(device)
        except UserDevice.DoesNotExist:
            UserDevice.objects.filter(user=request.user).delete()
            
            serializer.object.user = request.user
            serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def get_invitation(request):
    data = request.DATA.copy()


    trainer_authority = request.user.get_my_authority()

    if data.get('authorityId'):
        authority = get_object_or_404(Authority, id=data.get('authorityId'))
    else:
        authority = trainer_authority

    if not authority:
        return Response({'error': 'You have not authority'}, status=403)

    invite = authority.get_invite(status=data.get('status'), trainer_status=request.user.status, trainer_authority=trainer_authority)
    return Response(model_to_dict(invite))


@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def all_invitation(request):
    #data = request.DATA.copy()


    #trainer_authority = request.user.get_my_authority()

    queryset = Authority.objects.all()
    if not request.user.is_staff:
        authority_ids = filter_permitted_authority(request.user, subscribes=True)
        queryset = queryset.filter(id__in=authority_ids)

    workbook = xlwt.Workbook()
    for user_status, name in USER_STATUS_CHOICES:

        if not name:
            continue

        sheet = workbook.add_sheet(name)

        sheet.write(0, 0, u'พื้นที่')
        sheet.write(0, 1, u'รหัส')

        row = 1
        for authority in queryset:

            invite = authority.get_invite(
                status=request.GET.get('status') or USER_STATUS_ADDITION_VOLUNTEER,
                trainer_status=user_status,
                trainer_authority=authority
            )

            sheet.write(row, 0, authority.name)
            sheet.write(row, 1, invite.code)
            row += 1

    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % 'all-invitation-codes.xls'
    workbook.save(response)

    return response


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def chatroom_invites(request):
    body = request.DATA.copy()

    report_id = body.get('reportId')
    inviteList = body.get('inviteList')
    subject = body.get('subject')
    template = body.get('template') or u'คุณได้รับการเชิญเข้าร่วมปรึกษาเรื่อง {subject} เข้าร่วมห้องแชทได้ที่ http://www.cmonehealth.org/dashboard/fire/#/?token={token}'

    for invite in inviteList:
        inviteType = invite.get('type')
        if inviteType == 'podd':
            try:
                user = User.objects.get(id=invite.get('id'))
            except User.DoesNotExist:
                continue
            authority = user.authority_users.all()[0]
            token = create_token(request.user.domain_id, report_id, user.id, user.username, authority.id, authority.name)

            notification = Notification(
                receive_user=user,
                to=user.username,
                message=template.format(subject=subject, token=token),
            )
            notification.save()

        elif inviteType == 'anonymous':
            inviteName = invite.get('name')
            inviteTelno = invite.get('telno')
            inviteAuthorityName = invite.get('authorityName')

            origin_to = '%s %s' % (inviteName, inviteTelno)
            token = create_token(request.user.domain_id, report_id, 0, origin_to, 0, inviteAuthorityName)

            notification = Notification(
                to=inviteTelno,
                original_to=origin_to,
                anonymous_send=Notification.SMS_ONLY,
                message=template.format(subject=subject, token=token),
            )
            notification.save()

    return Response('{ "message": "ok" }', status=status.HTTP_200_OK)