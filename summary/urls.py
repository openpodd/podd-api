from django.conf.urls import patterns, include, url


urlpatterns = patterns('summary.views',
    url(r'monitor/', 'summary_report_for_monitor', name='summary_report_for_monitor'),
    url(r'list-volunteer/', 'summary_list_volunteer', name='summary_list_volunteer'),
    url(r'^(?P<summary_slug>\w+)/', 'summary_report', name='summary_report'),
)
