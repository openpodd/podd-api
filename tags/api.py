
from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from taggit.models import Tag
from tags.serializers import TagSerializer


@api_view(['GET']) 
def list_tags(request):
    queryset = Tag.objects.all()
    if request.GET.get('q'):
        queryset = queryset.filter(name__startswith=request.GET['q'])

    serializer = TagSerializer(queryset, many=True)

    return Response(serializer.data)