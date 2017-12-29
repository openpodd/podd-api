# -*- encoding: utf-8 -*-

import json
import re
from celery.contrib.methods import task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.template import Template, Context
from django.template.defaultfilters import striptags, truncatechars
from accounts.models import Authority, UserDevice, user_can_edit_basic_check, Configuration, User
from common.constants import NewsTypeChoices, NEWS_TYPE_NEWS, NOTIFICATION_SUPPORT_TEMPLATES, \
    NOTIFICATION_SUPPORT_TEMPLATE_PREFIX, NOTIFICATION_SUPPORT_TEMPLATE_SUFFIX
from common.functions import publish_gcm_message, publish_sms_message, publish_apns_message, \
    email_title_render_template, email_body_render_template, send_email_with_template, clean_phone_numbers, \
    get_system_user
from common.models import AbstractCommonTrashModel, DomainMixin
from common.pub_tasks import get_cache, set_cache

from plans.templatetags import plans_tags # dont' remove this line


class NotificationTemplate(DomainMixin):
    TYPE_REPORT = 1
    TYPE_REPORTER_FEEDBACK = 2
    TYPE_NOTIFY_FOLLOW_UP = 3
    TYPE_LATE_FOLLOW_UP = 4
    TYPE_PRIVATE = 5 # same as TYPE_REPORT but not share
    TYPE_DELAYED_FOLLOW_UP = 6
    TYPE_CHATROOM = 7

    TYPE_CHOICES = (
        (TYPE_REPORT, 'Report'),
        (TYPE_REPORTER_FEEDBACK, 'Reporter Feedback'),
        (TYPE_NOTIFY_FOLLOW_UP, 'Notify Follow Up'),
        (TYPE_LATE_FOLLOW_UP, 'Late Follow Up'),
        (TYPE_PRIVATE, 'Private'),
        (TYPE_DELAYED_FOLLOW_UP, 'Delayed Follow Up'),
        (TYPE_CHATROOM, 'Chat Room')
    )

    template = models.TextField()
    condition = models.TextField()
    description = models.TextField(null=True, blank=True)

    authority = models.ForeignKey(Authority, related_name='notice_template_authority')

    type = models.IntegerField(max_length=2, choices=TYPE_CHOICES, default=TYPE_REPORT)

    # For Notify Follow Up
    trigger_pattern = models.CharField(max_length=512, null=True, blank=True)
    trigger_delay_days = models.IntegerField(max_length=5, null=True, blank=True)

    # For Late Follow Up
    trigger_notify_follow_up = models.ForeignKey('self', related_name='late_follow_up', null=True, blank=True)

    accepted_plan = None

    # For Delayed follow up.
    delayed_time = models.FloatField(null=True, blank=True)

    delta = models.IntegerField(max_length=5, default=0)

    class Meta:
        ordering = ['-delta', 'id']

    def __unicode__(self):
        return '%s' % self.description or self.condition

    def user_can_edit(self, user):
        return user_can_edit_basic_check(user, self.authority.users.filter(id=user.id).count() > 0)

    def get_data(self):
        return type('NotificationTemplateData', (object,), json.loads(self.data))

    @property
    def send_reporter_only(self):
        return self.type in [self.TYPE_REPORTER_FEEDBACK, self.TYPE_NOTIFY_FOLLOW_UP]

    def enabled(self, authority):
        return NotificationAuthority.objects.filter(template=self, authority=authority).count() > 0

    def can_disable(self, authority):
        return not self.send_reporter_only or self.authority == authority

    def _can_fork(self, authority):
        pass_authority_ids = set([])
        return self.__can_fork(authority, False, pass_authority_ids)


    def __can_fork(self, authority, can, pass_authority_ids):

        # circular and duplicate check
        if authority.id in pass_authority_ids:
            return can
        pass_authority_ids.add(authority.id)

        if self.send_reporter_only:
            for child in authority.authority_inherits.all():

                can = can or NotificationTemplate.objects.filter(authority=child, id=self.id).count() > 0
                if can:
                    return can

                can = can or self.__can_fork(child, can, pass_authority_ids)

            return can

        return False


    def _fork(self, authority):

        forked_template = NotificationTemplate.objects.create(
            template=self.template,
            condition=self.condition,
            description=self.description,
            type=self.type,
            authority=authority
        )

        self.id = forked_template.id
        self.authority = authority


    def _disable_children(self, authority):
        pass_authority_ids = set([])
        self.__disable_children(authority, pass_authority_ids)

    def __disable_children(self, authority, pass_authority_ids):

        # circular and duplicate check
        if authority.id in pass_authority_ids:
            return
        pass_authority_ids.add(authority.id)

        for child in authority.authority_inherits.all():
            for nt in NotificationAuthority.objects.filter(authority=child, template=self):
                nt.delete()
            self.__disable_children(child, pass_authority_ids)


    def enable(self, authority, to=''):

        if self._can_fork(authority):
            self._disable_children(authority)
            self._fork(authority)

        pass_authority_ids = set([])
        self._enable(authority, pass_authority_ids)

        relation = NotificationAuthority.objects.get(template=self, authority=authority)

        if to:
            relation.to = to
            relation.save()

        return relation


    def _enable(self, authority, pass_authority_ids):

        # circular and duplicate check
        if authority.id in pass_authority_ids:
            return
        pass_authority_ids.add(authority.id)

        # Don't use get_or_create
        try:
            NotificationAuthority.objects.get(template=self, authority=authority)
        except NotificationAuthority.DoesNotExist:
            NotificationAuthority.objects.create(template=self, authority=authority)

        if self.send_reporter_only:
            for child in authority.authority_inherits.all():
                self._enable(child, pass_authority_ids)


    def disable(self, authority):
        pass_authority_ids = set([])
        self._disable(authority, authority, pass_authority_ids)

    def _disable(self, authority, disable_by, pass_authority_ids):


        # circular and duplicate check
        if authority.id in pass_authority_ids:
            return
        pass_authority_ids.add(authority.id)

        if not self.can_disable(disable_by):
            return

        for enabled in NotificationAuthority.objects.filter(template=self, authority=authority):
            enabled.delete()

        if self.send_reporter_only:
            for child in authority.authority_inherits.all():
                self._disable(child, disable_by, pass_authority_ids)

    def get_comment_render(self):
        return '[%d] %s' % (self.id, self.description)

    def save(self, *args, **kwargs):


        try:
            template = json.loads(self.template, strict=False)

        except ValueError:
            template = {
                'default': {
                    'subject': 'Unknow Subject',
                    'body': self.template
                }
            }

        if not template.get('email'):
            template['email'] = template['default']

        if not template.get('sms'):
            template['sms'] = template['default']['body']

        if not template.get('gcm'):
            template['gcm'] = template['default']['body']

        self.template = json.dumps(template, ensure_ascii=False, indent=4)

        if self.type == self.TYPE_NOTIFY_FOLLOW_UP:
            if not self.trigger_pattern:
                raise ValidationError({'trigger_pattern': ["This field is required"]})

            self.trigger_delay_days = self.trigger_delay_days or 1
            self.late_follow_up.all().update(condition=self.condition)


        if self.type == self.TYPE_LATE_FOLLOW_UP:
            if not self.trigger_notify_follow_up:
                raise ValidationError({'trigger_notify_follow_up': ["This field is required"]})
            self.condition = self.trigger_notify_follow_up.condition

        super(NotificationTemplate, self).save(*args, **kwargs)


class NotificationAuthority(AbstractCommonTrashModel, DomainMixin):
    template = models.ForeignKey(NotificationTemplate, related_name='notice_template')
    authority = models.ForeignKey(Authority, related_name='notice_authority')
    to = models.TextField(null=True, blank=True)


    #class Meta:
    #    unique_together = (('template', 'authority'),)

    def __unicode__(self):
        return '%s -- %s' % (self.authority.name, self.template)

    def save(self, *args, **kwargs):

        if not self.is_deleted:

            template = self.template

            check_duplicate_list = NotificationAuthority.objects.filter(template=template, authority=self.authority)
            if self.id:
                check_duplicate_list = check_duplicate_list.exclude(id=self.id)

            if check_duplicate_list.count() > 0:
                raise ValidationError('Template enabled by authority', code='invalid')

            if template.send_reporter_only:
                self.to = ''

        super(NotificationAuthority, self).save(*args, **kwargs)




class FollowUp(DomainMixin):
    """
    *@DynamicAttrs*
    """
    report = models.ForeignKey('reports.Report')

    # notification_authority = models.ForeignKey(NotificationAuthority, related_name='follow_up_notification_authority') # deprecate

    # Can't use notification_authority because when disable follow up will be delete
    template = models.ForeignKey(NotificationTemplate, related_name='follow_up_template')
    authority = models.ForeignKey(Authority, related_name='follow_up_authority')

    date = models.DateTimeField()
    deadline = models.DateTimeField(null=True, blank=True)

    notified = models.BooleanField(default=False) # for check send duplicate of date
    late_notified = models.BooleanField(default=False) # for check send duplicate of deadline

    responsed = models.BooleanField(default=False) # for check not send late notify if True

    disabled = models.BooleanField(default=False)


class Notification(DomainMixin):

    SMS_ONLY = 1
    EMAIL_ONLY = 2

    report = models.ForeignKey('reports.Report', null=True, blank=True)
    receive_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='receive_user', null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=100, choices=NewsTypeChoices, default=NEWS_TYPE_NEWS)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_created_by', null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    is_seen = models.BooleanField(default=False)

    notification_authority = models.ForeignKey(NotificationAuthority, related_name='notice_item_notice', null=True, blank=True)
    to = models.CharField(max_length=255)
    anonymous_send = models.IntegerField(null=True, blank=True)
    subscribe_authority = models.ForeignKey(Authority, related_name='subscribe_authority_notice', null=True, blank=True)

    # Cache attribute
    authority = None
    template = None
    plan = None

    class Meta:
        ordering = ['-created_at']

    def __unicode__(self):
        if self.notification_authority:
            return 'to: %s, report: %s, template.type: %s' % (self.to,
                                                              self.report,
                                                              self.notification_authority.template.type)
        else:
            return 'to: %s, report: %s' % (self.to, self.report)


    def init_message(self):
        self.authority = self.notification_authority.authority

        if self.notification_authority and self.notification_authority.template:
            template = self.notification_authority.template
            self.template = json.loads(template.template)
        else:
            self.template = {}

    def get_first_image_thumbnail_url(self):
        if not self.report or self.report.images.count() == 0:
            return None
        return self.report.images.all()[0].thumbnail_url

    def process_message(self, message):
        # TODO: render {{ param }} or [[ service ]]
        return message


    def get_message_context(self):

        chatroom_token = ''
        if self.notification_authority.template.type == NotificationTemplate.TYPE_CHATROOM:
            user_id = 0
            authority_id = 0
            authority_name = ''
            if self.receive_user:
                user_id = self.receive_user_id
                try:
                    user = User.objects.get(id=user_id)
                    firstAuthority = user.authority_users.all()[0]
                    authority_id = firstAuthority.id
                    authority_name = firstAuthority.name
                except User.DoesNotExist:
                    pass


            from reports.functions import chat_create_token

            room_id = self.report.id
            username = self.to

            if username != '@[chatroom]':
                cache_key = 'chattoken-%s-%s' % (room_id, username)
                chatroom_token = get_cache(cache_key)
                if not chatroom_token:
                    chatroom_token = chat_create_token(room_id, user_id, username, authority_id, authority_name)
                    set_cache(cache_key, chatroom_token)

        return Context({
            'report': self.report,
            'created_at': self.created_at,
            'seen_at': self.seen_at,
            'authority': self.authority,
            'notification': self,
            'to': self.to,
            'receive_user': self.receive_user,
            'created_by': self.created_by,
            'plan': self.plan,
            'chatroom_token': chatroom_token
        })

    def render_message(self, key, subkey=None):

        # For publish news
        if self.message:
            message = self.process_message(self.message)

            if key in ['sms', 'gcm', 'apns']:
                message = striptags(message)
            if subkey in ['subject', 'title', 'name']:
                message = message[0:80]

            return message

        elif self.type in NOTIFICATION_SUPPORT_TEMPLATES.keys():

            message = NOTIFICATION_SUPPORT_TEMPLATES[self.type]
            message = '%s %s %s' % (
                NOTIFICATION_SUPPORT_TEMPLATE_PREFIX,
                message,
                NOTIFICATION_SUPPORT_TEMPLATE_SUFFIX
            )

            return Template(message).render(self.get_message_context())

        # For notification template condition
        else:
            if self.template is None:
                self.init_message()

            template = self.template.get(key)

            if not template:
                return ''

            if subkey:
                template = template[subkey]

            return Template(template).render(self.get_message_context())


    def render_web_message(self):
        return self.render_message('default', 'body')


    @task()
    def publish_message(self):
        if not self.message and self.type not in NOTIFICATION_SUPPORT_TEMPLATES.keys():
            self.init_message()

        if not self.template and not self.message and self.type not in NOTIFICATION_SUPPORT_TEMPLATES.keys():
            return

        # Case have user in system
        if self.receive_user:

            if self.created_by == self.receive_user:
                return

            # Send email
            if self.receive_user.email:
                if settings.NOTIFICATION_DISABLED and settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
                    print '------ EMAIL PARAMS ------'
                    print '  -> subject: ', self.render_message('email', 'subject')
                    print '  -> body: ', self.render_message('email', 'body')
                    print '  -> to: ', self.receive_user.email
                    print '------ /EMAIL PARAMS -----'
                else:

                    authorities = Authority.objects.filter(users=self.receive_user)
                    authority = authorities[0] if authorities.count() else None

                    email_tile = email_title_render_template(self.render_message('email', 'subject'), authority)
                    email_body = email_body_render_template(self.render_message('email', 'body'),
                                                            self.receive_user,
                                                            authority)

                    send_email_with_template(email_tile, email_body, [self.receive_user.email])

                    # send_mail(
                    #     self.render_message('email', 'subject'),
                    #     self.render_message('email', 'body'),
                    #     settings.EMAIL_ADDRESS_NO_REPLY,
                    #     [self.receive_user.email],
                    # )

            # Send sms
            if 'SUPPORT_' not in self.type:
                tels = clean_phone_numbers(self.receive_user.telephone)
                if len(tels):
                    if not self.message:
                        self.message = self.render_message('sms')
                        super(Notification, self).save()
                    publish_sms_message(self.message, tels)

            report_id = self.report and self.report.id
            badge = Notification.objects.filter(receive_user=self.receive_user, is_seen=False).count()

            # Send gcm
            if not self.receive_user.is_anonymous or self.type == NEWS_TYPE_NEWS:
                try:
                    device = UserDevice.objects.get(user=self.receive_user)
                    publish_gcm_message([device.gcm_reg_id], self.render_message('gcm'), NEWS_TYPE_NEWS, self.id, report_id=report_id, badge=badge)
                    publish_apns_message([device.apns_reg_id], self.render_message('apns'), self.id, report_id=report_id, badge=badge)
                except UserDevice.DoesNotExist:
                    pass

        # Two case email or phone number
        else:
            if self.anonymous_send == self.SMS_ONLY:
                if not self.message:
                    self.message = self.render_message('sms')
                    super(Notification, self).save()
                publish_sms_message(self.message, clean_phone_numbers(self.to))
            elif self.anonymous_send == self.EMAIL_ONLY:
                if settings.NOTIFICATION_DISABLED and settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
                    print '------ EMAIL PARAMS ------'
                    print '  -> subject: ', self.render_message('email', 'subject')
                    print '  -> body: ', self.render_message('email', 'body')
                    print '  -> to: ', self.to
                    print '------ /EMAIL PARAMS -----'
                else:
                    send_mail(
                        self.render_message('email', 'subject'),
                        self.render_message('email', 'body'),
                        settings.EMAIL_ADDRESS_NO_REPLY,
                        [self.to],
                    )
            elif self.to == '@[chatroom]':
                chat_room_id = self.report.id
                system_user = get_system_user()
                chat_user_id = system_user.id
                chat_username = system_user.username
                chat_message = self.render_message('sms')

                meta = {}
                form_data = json.loads(self.report.form_data)
                if form_data['ct_latitude'] and form_data['ct_longitude']:
                    meta = {
                        'location': {
                            'lat': form_data['ct_latitude'],
                            'lng': form_data['ct_longitude']
                        }
                    }

                from reports.functions import chat_post_message
                chat_post_message(chat_room_id, chat_user_id, chat_username, chat_message, meta=meta)

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, **kwargs)
        self.publish_message.delay()
