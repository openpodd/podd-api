from django.core.management import BaseCommand

from logs.models import LogAction


class Command(BaseCommand):
    help = 'Create log action'

    def handle(self, *args, **options):
        # print self.help
        action, created = LogAction.objects.get_or_create(
            name='REPORT_CREATE',
        )
        action.template = 'Report #{{ log_item.object_id1 }} was created.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='REPORT_FLAG_CHANGE',
        )
        action.template = 'Report #{{ log_item.object_id1 }} flag was changed to {{ log_item.object2.get_priority_display }}.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='REPORT_SEND_MAIL_NEW_REPORT',
        )
        action.template = 'Report #{{ log_item.object_id1 }}\'s emails was sent to {{ log_item.data.emails }} after having new negative report.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='REPORT_SEND_MAIL_NEW_CASE',
        )
        action.template = 'Report #{{ log_item.object_id1 }}\'s emails was sent to {{ log_item.data.emails }} after having new case.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='USER_CREATE',
        )
        action.template = 'User `{{ log_item.object1.username }}` was created.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='USER_EDIT',
        )
        action.template = 'User `{{ log_item.object1.username }}` field `{{ log_item.data.field }}` \
            was changed from {{ log_item.data.old }} to {{ log_item.data.new }}.'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='USER_LOGIN_CODE',
        )
        action.template = 'User `{{ log_item.object1.username }}` logged in system by code'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='USER_IS_DELETED',
        )
        action.template = 'User `{{ log_item.object1.username }}` is mark as deleted by \
            `{{ log_item.object2.username }}`'
        action.save()

        action, created = LogAction.objects.get_or_create(
            name='DASHBOARD_VIEW',
        )
        action.template = 'User `{{ log_item.object1.username }}` view dashboard `{{ log_item.data.path }}`'
        action.save()
