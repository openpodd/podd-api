from rest_framework import filters
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from areas.models import Place
from areas.serializers import PlaceSerializer


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    model = Place
    serializer_class = PlaceSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('category__code',)

    paginate_by = 2000
    paginate_by_param = 'page_size'

    def get_queryset(self):
        queryset = Place.objects.all().order_by('uuid')
        return queryset