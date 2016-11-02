from django.conf.urls import patterns, url


urlpatterns = patterns('reports.views',
    url(r'^administration-areas/$', 'search_nearby_area', name='search_nearby_area'),
    url(r'^(?P<report_id>[\w-]+)/share/$', 'report_share', name='report_share'),

)
