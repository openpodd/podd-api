
from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from monitorings.models import Monitoring
from monitorings.serializers import MonitorSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def list_monitoring(request):
    if not request.user.is_staff:
        return Response({u'detail': u'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    queryset = Monitoring.objects.all()
    serializer = MonitorSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def upload_monitoring(request):
    # bypass, do nothing.
    return Response({}, status=status.HTTP_200_OK)
