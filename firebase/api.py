import firebase_admin
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from firebase_admin import auth
from django.http import JsonResponse, Http404, HttpResponseBadRequest

from accounts.models import User


@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, ))
def obtain_firebase_token(request):
    uid = request.user.username
    firebase_token = auth.create_custom_token(uid)
    return JsonResponse({
        'username': uid,
        'domainId': request.user.domain_id,
        'id': request.user.id,
        'firebase_token': firebase_token,
        'authorities': [],
    })

@api_view(['POST'])
def podd_auth(request):
    username = request.DATA.get('username', '')
    password = request.DATA.get('password', '')

    try:
        user = User.objects.get(username=username)
    except (ValueError, User.DoesNotExist):
        return HttpResponseBadRequest()

    if not user.is_active or user.is_deleted:
        return HttpResponseBadRequest()

    if not user.check_password(password):
        return HttpResponseBadRequest()

    token, created = Token.objects.get_or_create(user=user)

    app = firebase_admin.get_app(name='podd')
    firebase_token = auth.create_custom_token(str(user.id), app=app)

    authorities = []
    for authority in user.authority_users.all():
        authorities.append({
            'id': authority.id,
            'name': authority.name
        })
    parties = []
    for party in user.party_set.all():
        parties.append({
            'id': party.id,
            'name': party.name
        })

    return JsonResponse({
        'username': user.username,
        'domainId': user.domain_id,
        'id': user.id,
        'firebaseToken': firebase_token,
        'token': token.key,
        'authorities': authorities,
        'parties': parties
    })