
from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mentions.models import Mention
from mentions.serializers import MentionSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def list_mention(request):
    queryset = Mention.objects.filter(mentionee=request.user).order_by('-created_at')[:5]
    serializer = MentionSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def seen_mention(request):
    mention_id = request.DATA.get('mentionId')
    if mention_id:
        try:
            mention = Mention.objects.get(id=mention_id, mentionee=request.user)
        except:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        if not mention.is_notified:
            mention.is_notified = True
            mention.seen_at = timezone.now();
            mention.save()

    return Response()