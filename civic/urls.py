from django.conf.urls import patterns, url, include
from rest_framework import routers
from civic import api

router = routers.DefaultRouter()

router.register(r'config/letter', api.LetterFieldConfigurationViewSet)

urlpatterns = patterns(
    'civic.views',
    url(r'letter/(?P<report_id>[\w-]+)/', 'letter', name='civic_letter'),
    url(r'^reports/(?P<status>.+)/', 'list_civic_report', name='civic_report_list'),
    url(r'^accomplishments/', 'accomplishments', name="civic_accomplishments"),
    url(r'^report/(?P<report_id>[\w-]+)/', 'display_civic_report', name='civic_report_display'),
    url(r'^', include(router.urls)),
)
