from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from firebase_admin import auth
from django.http import JsonResponse


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def obtain_firebase_token(request):
    uid = request.user.username
    firebase_token = auth.create_custom_token(uid)
    return JsonResponse({
        'username': uid,
        'id': request.user.id,
        'firebase_token': firebase_token,
        'authorities': [],

    })