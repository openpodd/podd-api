from django.conf.urls import patterns, url


urlpatterns = patterns('supervisors.views',
    url(r'^$', 'supervisors_home', name='supervisors_home'),
    url(r'^users/$', 'supervisors_users', name='supervisors_users'),
    url(r'^users/authorities/$', 'supervisors_authorities', name='supervisors_authorities'),
    url(r'^users/(?P<user_status>[a-z-_]+)/$', 'supervisors_users_by_status', name='supervisors_users_by_status'),
    url(r'^users/(?P<user_status>[a-z-_]+)/areas/(?P<area_id>\d+)/$', 'supervisors_users_by_area_and_status', name='supervisors_users_by_area_and_status'),
    url(r'^users/(?P<user_id>\d+)/edit/$', 'supervisors_users_edit', name='supervisors_users_edit'),
    url(r'^users/areas/(?P<area_id>\d+)/$', 'supervisors_users_by_area', name='supervisors_users_by_area'),
    
    url(r'^users/authorities/export/$', 'supervisors_export_users_excel_to_authorities', name='supervisors_export_users_excel_to_authorities'),
    
    url(r'^authorities/new/$', 'supervisors_new_authorities', name='supervisors_new_authorities'),
    url(r'^authorities/invitation-code/print/$', 'supervisors_authorities_print_invitation_code', name='supervisors_authorities_print_invitation_code'),
    url(r'^authorities/(?P<authority_id>\d+)/edit/$', 'supervisors_authorities_edit', name='supervisors_authorities_edit'),
 
    url(r'^logs/reports/$', 'supervisors_logs_reports', name='supervisors_logs_reports'),
    url(r'^logs/reports/report/(?P<report_id>\d+)/$', 'supervisors_logs_reports_by_report', name='supervisors_logs_reports_by_report'),
    url(r'^logs/reports/user/(?P<user_id>\d+)/$', 'supervisors_logs_reports_by_user', name='supervisors_logs_reports_by_user'),
    url(r'^logs/users/$', 'supervisors_logs_users', name='supervisors_logs_users'),
    url(r'^logs/users/user/(?P<user_id>\d+)/$', 'supervisors_logs_user', name='supervisors_logs_user'),

    url(r'^reports/investigation/(?P<investigation_id>\d+)/delete/', 'supervisors_report_investigation_delete', name='supervisors_report_investigation_delete'),
    url(r'^reports/investigation/(?P<investigation_id>\d+)/edit/', 'supervisors_report_investigation_edit', name='supervisors_report_investigation_edit'),
    url(r'^reports/investigation/add/', 'supervisors_report_investigation_create', name='supervisors_report_investigation_create'),
    url(r'^reports/investigation/', 'supervisors_report_investigation', name='supervisors_report_investigation'),

    url(r'^reports/laboratory/(?P<case_id>\d+)/delete/', 'supervisors_report_laboratory_delete', name='supervisors_report_laboratory_delete'),
    url(r'^reports/laboratory/(?P<case_id>\d+)/edit/', 'supervisors_report_laboratory_edit', name='supervisors_report_laboratory_edit'),
    url(r'^reports/laboratory/add/', 'supervisors_report_laboratory_create', name='supervisors_report_laboratory_create'),
    url(r'^reports/laboratory/', 'supervisors_report_laboratory', name='supervisors_report_laboratory'),

    url(r'^reports/laboratory-cause/(?P<cause_id>\d+)/delete/', 'supervisors_report_laboratory_cause_delete', name='supervisors_report_laboratory_cause_delete'),
    url(r'^reports/laboratory-cause/', 'supervisors_report_laboratory_cause', name='supervisors_report_laboratory_cause'),
)
