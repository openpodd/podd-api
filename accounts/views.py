# -*- encoding: utf-8 -*-
import xlwt

import collections

from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import redirect

from django.utils.http import urlsafe_base64_decode

from django.contrib.auth.models import Group

from accounts.models import User, GroupAdministrationArea, UserCode
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA, GROUP_WORKING_TYPE_REPORT_TYPE
from reports.models import AdministrationArea


def account_password_reset(request, uidb64=None, token=None):

    code = request.GET.get('code', '')

    if not code:
        return HttpResponse('code is not found.', status=400)

    UserModel = get_user_model()

    try:
        uid_int = urlsafe_base64_decode(uidb64)
        user = UserModel.objects.get(id=uid_int)
    except (ValueError, UserModel.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        user_authen = authenticate(username=user.username, code=code, ignore_password=True)
        if not user_authen:
            return HttpResponse('code is wrong or expired.', status=400)

        auth_login(request, user_authen)
        user_codes = UserCode.objects.filter(user=user_authen)
        user_codes.update(is_used = True)
        return redirect('/')
    else:
        return HttpResponse('invalid link', status=404)
