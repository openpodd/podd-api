from re import sub
from rest_framework.authtoken.models import Token
from accounts.models import User
from common.models import Domain

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








