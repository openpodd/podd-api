from django.conf.urls import patterns, url

from accounts.forms import LoginForm


urlpatterns = patterns('',
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'accounts.views.account_password_reset', name='account_password_reset'),
    # url(r'authorities-export/', 'accounts.views.export_excel_users_authorities', name='export_excel_users_authorities'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'authentication_form': LoginForm}, name='accounts_login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/accounts/login/'}, name='accounts_logout'),
)
