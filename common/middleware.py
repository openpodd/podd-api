from re import sub
from rest_framework.authtoken.models import Token
from accounts.models import User, Authority
from common.models import Domain
from django.dispatch import receiver
from crum import get_current_request
from crum.signals import current_user_getter


@receiver(current_user_getter)
def force_domain_user(sender, **kwargs):
    request = get_current_request()
    if request:
        header_token = request.META.get('HTTP_AUTHORIZATION', None)
        cross_domain = request.META.get('HTTP_CROSS_DOMAIN', None)
        if request.path == '/reports/' and \
                request.method == 'POST' and \
                header_token is not None and \
                cross_domain is not None:
            try:
                token = sub('Token ', '', header_token)
                token_obj = Token.objects.get(key=token)
                user = token_obj.user

                domain = Domain.objects.get(pk=cross_domain)
                if domain.id != user.domain_id:
                    public_user = User.default_manager.get(username='public-%s' % (domain.id,))
                    return public_user, 0
                return user, 0
            except Token.DoesNotExist:
                return None, 0
        else:
            return False, 0
    else:
        return False, 0


def switch_domain(request):

    user = None

    header_token = request.META.get('HTTP_AUTHORIZATION', None)
    if header_token is not None:
        try:
            token = sub('Token ', '', request.META.get('HTTP_AUTHORIZATION', None))
            token_obj = Token.objects.get(key=token)
            user = token_obj.user
        except Token.DoesNotExist:
            pass

    #print request.user

    if not user or (user and not user.id):
        return

    # TODO: clear domain from request host
    if False and request.path in ['/api-token-auth/', '/configuration/', '/admin/login/', '/api-auth/login/']:
        # print 'in path'

        # print request.get_host()

        try:
            domain = user.domains.get(code__contains=request.get_host())
            # print domain
            # print 'xxxxxx', user

            if domain and user.domain != domain:

                # print 'switch'

                user.domain = domain
                user.save()

                device = user.device
                if device:
                    device.domain = domain
                    device.save()

                # print '## Switch domain to', domain


        except Domain.DoesNotExist:
            pass
            # print 'user not registered on %s' % request.get_host()


    if not request.user.id:
        request.user = user


class SwitchDomainMiddleware(object):
    """Middleware to capture the request and user from the current thread."""

    def process_request(self, request):
        # print 'process_request'
        switch_domain(request)

    #def process_response(self, request, response):
    #    print 'process_response'
    #    switch_domain(request)
    #    return response








