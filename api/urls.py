# API REFERENCE: http://docs.poddapi.apiary.io/

from django.conf.urls import patterns, include, url

from rest_framework import routers

import summary
from flags import api as flags_api
from notifications import api as notifications_api
from reports import api as reports_api
from accounts import api as accounts_api
from plans import api as plans_api
from areas import api as areas_api
from summary import api as summary_api
from civic import api as civic_api

router = routers.DefaultRouter()

router.register(r'users', accounts_api.UserViewSet)
router.register(r'authorities', accounts_api.AuthorityViewSet)

router.register(r'reportStates', reports_api.ReportStateViewSet)
router.register(r'caseDefinitions', reports_api.CaseDefinitionViewSet)
router.register(r'reports', reports_api.ReportViewSet)
router.register(r'reportTypeCategories', reports_api.ReportTypeCategoryViewSet)
router.register(r'reportTypes', reports_api.ReportTypeViewSet)
router.register(r'recordSpecs', reports_api.RecordSpecViewSet)
router.register(r'reportAccomplishments', reports_api.ReportAccomplishmentViewSet)
router.register(r'aggregateReports', summary_api.AggregateReportViewSet)
router.register(r'reportComments', reports_api.ReportCommentViewSet)
router.register(r'flags', flags_api.FlagViewSet)
router.register(r'administrationArea', reports_api.AdministrationAreaViewSet)
router.register(r'notificationTemplates', notifications_api.NotificationTemplateViewSet)
router.register(r'notificationAuthorities', notifications_api.NotificationAuthorityViewSet)
router.register(r'notifications', notifications_api.NotificationViewSet)
router.register(r'plans', plans_api.PlanViewSet)
router.register(r'planReports', plans_api.PlanReportViewSet)
router.register(r'animalCauses', reports_api.AnimalLaboratoryCauseViewSet)
router.register(r'reportLaboratoryItems', reports_api.ReportLaboratoryItemViewSet)
router.register(r'civicletterconfig', civic_api.LetterFieldConfigurationViewSet)
urlpatterns = patterns('',
    url(r'^api-token-auth/', 'accounts.api.obtain_auth_token', name='obtain_auth_token'),
    url(r'^line-token-auth/', 'accounts.api.line_login_obtain_auth_token', name='line_login_obtain_auth_token'),
    url(r'^update-line-id/', 'accounts.api.update_line_id', name='update_line_id'),
    url(r'^validate-token/', 'accounts.api.validate_token', name='validate_token'),
    url(r'^firebase/token', 'firebase.api.obtain_firebase_token', name='obtain_firebase_token'),
    url(r'^firebase/podd/auth', 'firebase.api.podd_auth', name='firebase_podd_auth'),
    url(r'^configuration/', 'accounts.api.configuration', name='configuration'),
    url(r'^party/join/(?P<join_code>[0-9]+)', 'accounts.api.join_party', name='join_party'),
    url(r'^party/check/(?P<join_code>[0-9]+)', 'accounts.api.get_party', name='get_party_by_join_code'),
    url(r'^gcm/', 'accounts.api.gcm_registration', name='gcm_registration'),
    # url(r'^users/register/facebook-connect/(?P<domain_id>[0-9]+)/', 'accounts.api.facebook_connect', name='facebook_connect'),
    url(r'^users/administrationArea/', 'reports.api.get_default_administration_area', name='get_default_administration_area'),
    url(r'^users/register/device/(?P<domain_id>[0-9]+)/', 'accounts.api.user_register_by_user_device', name='user_register_by_user_device'),
    url(r'^users/register/group/code/', 'accounts.api.get_group_by_invitation_code', name='get_group_by_invitation_code'),
    url(r'^users/register/authority/code/', 'accounts.api.get_authority_by_invitation_code', name='get_authority_by_invitation_code'),
    url(r'^users/register/group/', 'accounts.api.user_register_by_group', name='user_register_by_group'),
    url(r'^users/register/authority/', 'accounts.api.user_register_by_authority', name='user_register_by_authority'),
    url(r'^users/code-login/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'accounts.api.user_code_login', name='user_code_login'),
    url(r'^users/forgot-password/', 'accounts.api.user_forgot_password', name='user_forgot_password'),
    url(r'^users/search/', 'accounts.api.users_search', name='users_search'),
    url(r'^users/volunteer/visualization/', 'accounts.api.visualization_volunteer_user', name='visualization_volunteer_user'),
    url(r'^users/profile/upload/', 'accounts.api.upload_image_profile', name='upload_image_profile'),
    url(r'^users/profile/device/', 'accounts.api.update_device', name='user_update_device'),
    url(r'^users/profile/password/', 'accounts.api.update_password', name='user_update_password'),
    url(r'^users/profile/', 'accounts.api.user_profile', name='user-profile'),
    url(r'^users/domains/', 'accounts.api.user_domains', name='user_domains'),
    url(r'^users/get-invitation/', 'accounts.api.get_invitation', name='user_get_invitation'),
    url(r'^users/all-invitation/', 'accounts.api.all_invitation', name='user_all_invitation'),
    url(r'^users/chatroom-invites/', 'accounts.api.chatroom_invites', name='user_chatroom_invite'),

    url(r'^users/(?P<pk>[0-9]+)/profile/upload/', 'accounts.api.upload_image_profile', name='upload_image_profile'),
    url(r'^users/(?P<pk>[0-9]+)/profile_image', 'accounts.api.profile_image', name='profile_image'),


    url(r'^authorities/(?P<parent_pk>[0-9]+)/notificationTemplates/$', notifications_api.AuthorityNotificationTemplateViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    url(r'^authorities/(?P<parent_pk>[0-9]+)/notificationTemplates/(?P<status>(enabled|disabled|cannotDisable)+)/', notifications_api.AuthorityNotificationTemplateViewSet.as_view({
        'get': 'list',
    })),
    url(r'^authorities/(?P<parent_pk>[0-9]+)/notificationTemplates/(?P<pk>[0-9]+)/enable/$', notifications_api.AuthorityNotificationTemplateViewSet.as_view({
        'post': 'enable',
    })),
    url(r'^authorities/(?P<parent_pk>[0-9]+)/notificationTemplates/(?P<pk>[0-9]+)/disable/$', notifications_api.AuthorityNotificationTemplateViewSet.as_view({
        'post': 'disable',
    })),

    url(r'^list-configuration/', 'accounts.api.list_configuration', name='list_configuration'),
    url(r'^list-group-structure/', 'accounts.api.list_group_structure', name='list_group_structure'),
    url(r'^ping/', 'accounts.api.ping', name='ping'),

    url(r'^mentions/seen/', 'mentions.api.seen_mention', name='mention-seen'),
    url(r'^mentions/', 'mentions.api.list_mention', name='mention-list'),

    url(r'^feed/mine', 'feed.api.items_list_mine', name='feed_list_mine'),
    url(r'^feed/', 'feed.api.items_list', name='feed_list'),

    url(r'^places/$', areas_api.PlaceViewSet.as_view({
        'get': 'list'
    })),

    url(r'^analysis/export/', 'analysis.api.export_analysis_csv', name='export_analysis_csv'),

    url(r'^reports/search/', 'reports.api.reports_search', name='reports_search'),
    url(r'^reportImage/upload/', 'reports.api.upload_report_image', name='upload_report_image'),
    url(r'^reportImages/', 'reports.api.add_report_image', name='add_report_image'),
    url(r'^report/location/(?P<guid>[-\w]+)/', 'reports.api.upd_report_location', name='update_report_location'),
    url(r'^report/summary/month/', 'reports.api.reports_summary_by_month', name='reports_summary_by_month'),
    url(r'^report/protect-create-with-state/(?P<key>[.\w-]+)/(?P<state>[\w-]+)/(?P<case>[\w-]+)/', 'reports.api.report_protect_create_with_state', name='report_protect_create_with_state'),
    url(r'^report/(?P<report_id>\d+)/protect-update-state/(?P<key>[.\w-]+)/(?P<state>[\w-]+)/(?P<case>[\w-]+)/', 'reports.api.report_protect_update_state', name='report_protect_update_state'),
    url(r'^report/(?P<report_id>\d+)/protect-verify-case/(?P<key>[.\w-]+)/(?P<verified>[\w-]+)/', 'reports.api.report_protect_verify_to_suspect_outbreak', name='report_protect_verify_to_suspect_outbreak'),

    url(r'^supports/', 'reports.api.add_support', name='report_add_support'),
    url(r'^reportTags/', 'reports.api.add_reports_tags', name='add_reports_tags'),

    url(r'^summary/users/performance/', 'summary.api.summary_by_show_performance_user', name='summary_by_show_performance_user'),
    url(r'^summary/users/daily-performance/', 'summary.api.daily_summary_performance_user', name='daily_summary_performance_user'),
    url(r'^summary/users/inactive/', 'summary.api.summary_by_inactive_person', name='summary_by_inactive_person'),
    url(r'^summary/monthly/', 'summary.api.monthly_summary', name='monthly_summary'),
    url(r'^summary/areas/count-reports/', 'summary.api.summary_by_number_of_report', name='summary_by_number_of_report'),
    url(r'^summary/areas/show-detail/', 'summary.api.summary_by_show_area_detail', name='summary_by_show_area_detail'),
    url(r'^summary/authorities/show-detail/', 'summary.api.summary_by_show_authority_detail', name='summary_by_show_authority_detail'),
    url(r'^summary/reports/', 'summary.api.summary_by_report_detail', name='summary_by_report_detail'),
    url(r'^summary/reports-visualization/', 'summary.api.summary_report_visualization', name='summary_report_visualization'),
    url(r'^summary/dashboard-visualization/', 'summary.api.summary_dashboard_visualization', name='summary_dashboard_visualization'),
    url(r'^summary/authority-dashboard/', 'summary.api.summary_report_by_authority', name='summary_report_by_authority'),
    url(r'^summary/aggregateReport/run/(?P<id>\d+)/$', 'summary.api.run_aggregate_report', name='summary_aggregate_report_run'),
    url(r'^summary/aggregateReport/result/(?P<name>.+)/', 'summary.api.serve_aggregate_report', name='summary_serve_aggregate_report'),
    url(r'^pages/fetch/', 'pages.api.proxy_fetch', name='pages_proxy_fetch'),
    url(r'^pages/dashboard/', 'pages.api.dashboard', name='pages_dashboard'),
    url(r'^services/broadcast_via_gcm', 'services.api.broadcast_via_gcm', name='services_broadcast_via_gcm'),

    url(r'^log/dashboard/view', 'pages.api.log_dashboard_view', name='log_dashboard_view'),

    url(r'^tags/list/', 'tags.api.list_tags', name='list_tags'),

    # url(r'^notifications/import/', 'notifications.api.import_notifications', name='notifications-import'),
    url(r'^notifications/seen/', 'notifications.api.seen_notification', name='notification-seen'),

    url(r'^dashboard/villages/', 'reports.api.dashboard_villages', name='dashboard_villages'),

    url(r'^funf/upload/', 'monitorings.api.upload_monitoring', name='monitoring-upload'),
    url(r'^funf/', 'monitorings.api.list_monitoring', name='monitoring-list'),


    url(r'^administrationArea/contacts/update/', 'reports.api.update_administration_area_contacts', name='update_administration_area_contacts'),
    url(r'^administrationArea/contacts/', 'reports.api.view_administration_area_contacts', name='view_administration_area_contacts'),

    url(r'^notifications/test/', 'notifications.api.test_send_notifications', name='notification-test'),

    url(r'^reportLaboratoryFiles/(?P<file_id>\d+)/', 'reports.api.delete_file_to_laboratory', name='delete_file_to_laboratory'),
    url(r'^reportLaboratoryFiles/', 'reports.api.upload_file_to_laboratory', name='upload_file_to_laboratory'),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^test-dodd/(?P<report_id>\d+)/', 'dodd.views.test_link_report', name='test_dodd'),
    url(r'^covid/monitoring/', 'covid.views.list_monitoring', name='covid_list'),
    url(r'^covid/summary/(?P<authority_id>\d+)', 'covid.views.daily_summary', name='covid_list'),
    url(r'^civic/letter/(?P<report_id>[\w-]+)/', 'civic.views.letter', name='civic_letter'),
    url(r'^civic/reports/(?P<status>.+)/', 'civic.views.list_civic_report', name='civic_report_list'),
    url(r'^civic/accomplishments/', 'civic.views.accomplishments', name="civic_accomplishments"),
    url(r'^civic/report/(?P<report_id>[\w-]+)/', 'civic.views.display_civic_new_report', name='civic_report_display'),
    url(r'^civic/success_report/(?P<report_id>[\w-]+)/', 'civic.views.display_civic_success_report', name='civic_success_report_display'),
    url(r'^', include(router.urls)),
)

