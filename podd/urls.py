from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^accounts/', include('accounts.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^reports/', include('reports.urls')),
    url(r'^supervisors/', include('supervisors.urls')),
    url(r'', include('api.urls')),
    url(r'^summary/', include('summary.urls')),
    url(r'^public/$', 'reports.views.report_share', name='public'),

                       )


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
