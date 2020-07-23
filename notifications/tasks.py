import datetime
import logging

from crum import set_current_user
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from common.constants import NEWS_TYPE_NEWS
from common.functions import get_system_user, publish_sms_message, clean_phone_numbers, clean_emails

from common.models import Domain

from notifications.models import FollowUp, Notification, NotificationAuthority, NotificationTemplate
from podd.celery import app


@app.task
def send_alert_follow_up():
    for domain in Domain.objects.all():
        system_user = get_system_user()
        system_user.domain = domain
        set_current_user(system_user)

        _send_alert_follow_up()


def _send_alert_follow_up():
    today = timezone.now()
    yesterday = today - datetime.timedelta(minutes=settings.MINUTES_PER_DAY)

    for follow_up in FollowUp.objects.filter(date__gt=yesterday,
                                             date__lte=today,
                                             notified=False,
                                             template__type=NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP).exclude(disabled=True):

        report = follow_up.report
        reporter = report.created_by

        try:
            notification_authority = NotificationAuthority.objects.get(template=follow_up.template,
                                                                       authority=follow_up.authority)
        except NotificationAuthority.DoesNotExist:
            continue

        notification_data = {
            'report': report,
            'notification_authority': notification_authority,
            'receive_user': reporter,
            'to': reporter.username,
            'type': NEWS_TYPE_NEWS,
        }
        Notification.objects.create(**notification_data)
        follow_up.notified = True
        follow_up.save()

    late_follow_up_list = FollowUp.objects.filter(deadline__gt=yesterday,
                                                  deadline__lte=today,
                                                  late_notified=False,
                                                  responsed=False,
                                                  template__type=NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP).exclude(disabled=True)
    for deadline in late_follow_up_list:
        report = deadline.report
        report.create_report_notification(types=[NotificationTemplate.TYPE_LATE_FOLLOW_UP])
        deadline.late_notified = True
        deadline.save()


@app.task
def send_delayed_follow_up():
    for domain in Domain.objects.all():
        system_user = get_system_user()
        system_user.domain = domain
        set_current_user(system_user)

        _send_delayed_follow_up(logging.getLogger(__name__), domain)


def _send_delayed_follow_up(logger, domain):
    period_end = timezone.now()

    threshold = settings.NOTIFICATION_THRESHOLDS
    delayed_follow_up_check_period = threshold.get('delayed_follow_up_check_period', datetime.timedelta(minutes=15))
    period_start = period_end - delayed_follow_up_check_period

    candidate_follow_up_items = FollowUp.objects.filter(date__gt=period_start,
                                                        date__lte=period_end,
                                                        disabled=False,
                                                        notified=False,
                                                        template__type=NotificationTemplate.TYPE_DELAYED_FOLLOW_UP)

    logger.debug('> %s Check, period_start: %s, period_end: %s' % (domain, period_start, period_end))
    logger.debug('> %s Found %d candidate follow up' % (domain, candidate_follow_up_items.count()))
    for item in candidate_follow_up_items:
        # Evaluate template condition on report.
        if item.report.check_report_condition(item.template.condition):
            try:
                notification_authority = NotificationAuthority.objects.get(template=item.template,
                                                                           authority=item.authority)
            except NotificationAuthority.DoesNotExist:
                continue

            try:
                item.report.create_notification(
                    notification_template_accepted_list=(item.template,),
                    authority=notification_authority.authority
                )

                item.notified = True
                item.save()
            except Exception as e:
                logger.error('> %s Process task fail' % domain)
                logger.error(e)


@app.task
def test_send_notification(type, users, subject='[test]', message='test send notification.'):

    if type == Notification.SMS_ONLY:
        to_telephones = clean_phone_numbers(users)
        if not to_telephones:
            return

        publish_sms_message(message, to_telephones)

    elif type == Notification.EMAIL_ONLY:
        to_emails = clean_emails(users)
        if not to_emails:
            return

        if settings.NOTIFICATION_DISABLED and settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
            print '------ EMAIL PARAMS ------'
            print '  -> subject: ', subject
            print '  -> body: ', message
            print '  -> to: ', to_emails
            print '------ /EMAIL PARAMS -----'
        else:
            send_mail(
                subject,
                message,
                settings.EMAIL_ADDRESS_NO_REPLY,
                to_emails,
            )


@app.task
def deregister_fcm_from_user_device(fcm_reg_id):
    from accounts.models import UserDevice

    if fcm_reg_id:
        for device in UserDevice.objects.filter(fcm_reg_id=fcm_reg_id):
            device.fcm_reg_id = None
            device.save()
