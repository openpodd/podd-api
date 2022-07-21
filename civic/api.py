from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from civic.models import LetterFieldConfiguration
from civic.serializers import LetterFieldConfigurationSerializer
from common.constants import USER_STATUS_COORDINATOR, USER_STATUS_PUBLIC_HEALTH


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and ( user.status == USER_STATUS_COORDINATOR or user.status == USER_STATUS_PUBLIC_HEALTH)


class LetterFieldConfigurationViewSet(viewsets.ModelViewSet):
    model = LetterFieldConfiguration
    serializer_class = LetterFieldConfigurationSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, UserPermission,)

    def get_queryset(self):
        user = self.request.user
        authority = user.get_my_authority()
        query = LetterFieldConfiguration.objects.filter(authority=authority)
        code = self.request.QUERY_PARAMS.get('code')
        if code:
            query = query.filter(code=code)
        return query

    def pre_save(self, obj):
        if not hasattr(obj, 'authority'):
            user = self.request.user
            authority = user.get_my_authority()
            obj.authority = authority
