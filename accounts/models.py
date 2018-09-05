# -*- encoding: utf-8 -*-
import copy
import datetime
from random import randint
from django.core.exceptions import ValidationError
import uuid 
import json

from cacheops import invalidate_all

from celery.contrib.methods import task_method

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import IntegrityError
from django.contrib.gis.db import models
from django.db.models import Q, Count
from django.db.models.signals import m2m_changed
from django.utils import timezone

from taggit.managers import TaggableManager

from common.constants import GROUP_WORKING_TYPE_CHOICES, USER_STATUS_CHOICES, USER_STATUS_VOLUNTEER, \
    USER_STATUS_ADDITION_VOLUNTEER
from common.decorators import domain_celery_task
from common.models import DomainMixin, DomainManager, Domain, MultiDomainMixin, AbstractCommonTrashModel
from podd.celery import app, DomainTask


class MixUserManager(UserManager, DomainManager):
    pass

class UserNotificationMixin(models.Model):
    send_channel_sms   = models.BooleanField(default=True)
    send_channel_email = models.BooleanField(default=True)
    send_channel_alert = models.BooleanField(default=True)

    send_type_report   = models.BooleanField(default=True)
    send_type_comment = models.BooleanField(default=True)
    send_type_like = models.BooleanField(default=True)
    send_type_me_too = models.BooleanField(default=True)


    class Meta:
        abstract = True


    def save(self, *args, **kwargs):

        if self.is_public:
            self.send_channel_sms = False

        super(UserNotificationMixin, self).save(*args, **kwargs)



class User(AbstractUser, MultiDomainMixin, UserNotificationMixin, AbstractCommonTrashModel):
    is_anonymous = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    fbuid = models.CharField(blank=True, null=True, max_length=255, unique=True)
    contact = models.TextField(blank=True, verbose_name=u'ที่อยู่')
    telephone = models.CharField(max_length=100, blank=True, verbose_name=u'เบอร์โทรศัพท์ส่วนตัว')
    project_mobile_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=u'เบอร์โทรศัพท์โครงการ')
    administration_area = models.ForeignKey('reports.AdministrationArea', related_name='users', null=True, blank=True)
    avatar_url = models.URLField(max_length=300, blank=True, null=True)
    thumbnail_avatar_url = models.URLField(max_length=300, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True)
    running_number = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    display_password = models.CharField(max_length=128, blank=True, default='', verbose_name=u'รหัสผ่าน')

    status = models.CharField(max_length=100, choices=USER_STATUS_CHOICES, blank=True, default='', verbose_name=u'สถานะผู้ใช้')

    trainer_authority = models.ForeignKey('accounts.Authority', blank=True, null=True, related_name='user_trainer_authority', verbose_name=u'ถูกสอนโดยกลุ่ม')
    trainer_status = models.CharField(max_length=100, choices=USER_STATUS_CHOICES, blank=True, null=True, verbose_name=u'ถูกสอนโดยสถานะ')


    send_invitation = False
    _important_fields = ['username', 'first_name', 'last_name', 'project_mobile_number',
        'serial_number', 'running_number', 'note']

    objects = MixUserManager()

    graph_node = True
    graph_fields = ['status']

    @property
    def name(self):
        return self.get_full_name() or self.username

    def has_custom_permission(self, perm):
        if not self.is_active:
            return False

        return perm in self.get_all_custom_permissions()

    def get_report_count(self):
        return self.report_created_by.values_list('id').count()

    def get_support_count(self):
        return self.report_created_by.extra(select={'support_count': 'SUM(like_count + me_too_count)'})\
            .values('support_count').order_by('support_count')[0]['support_count'] or 0

    def get_category_count(self):
        from reports.models import ReportTypeCategory

        report_types = self.report_created_by.values('type').annotate(total=Count('type')).order_by('-total')

        result = []
        for category in ReportTypeCategory.objects.all():
            category_report_types = category.report_type_category.all().values_list('id', flat=True)
            answer = 0
            for report_type in report_types:
                if report_type['type'] in category_report_types:
                    answer += report_type['total']

            result.append({
                'name': category.name,
                'code': category.code,
                'count': answer
            })
        return result

    def get_all_custom_permissions(self):
        if not hasattr(self, '_perm_custom_cache'):
            self._perm_custom_cache = RoleCustomPermission.objects.all()
            if not self.is_staff:
                self._perm_custom_cache = self._perm_custom_cache.filter(role=self.status)
            self._perm_custom_cache = self._perm_custom_cache.values_list('role_custom_permissions__name', flat=True).distinct()
        return self._perm_custom_cache

    def get_my_authority(self):
        authority = self.authority_users.order_by('id')
        if authority:
            return authority[0]
        return None

    def get_authority(self):
        authority = self.authority_users.all()
        if authority:
            from accounts.serializers import AuthorityListSerializer
            return AuthorityListSerializer(authority[0]).data
        return None

    def save(self, *args, **kwargs):

        is_new = not self.id
        if is_new:

            if not self.username:

                if self.is_anonymous:
                    name = 'Anonymous%s' % '{0:09d}'.format(randint(0, 999999999))
                    self.username = name
                    self.first_name = name
                else:
                    self.username = self.email or self.telephone or self.serial_number or None

                if not self.password:
                    password = self.display_password or self.telephone or self.serial_number or self.username
                    self.set_password(password)

            if self.send_invitation:
                pass
                # TODO: send sms and email invitation
                # May be include password or direct link login to change password

        super(User, self).save(*args, **kwargs)

    def user_can_edit(self, user):

        if user and user.is_authenticated():
            if user.is_staff or self.id == user.id:
                return True

            elif user.status in [USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER]:
                return False

            else:
                from common.functions import filter_permitted_users
                return self.id in filter_permitted_users(user, subscribes=False)

        # Admin Authorities
        # authority_ids = self.authority_users.values_list('id')
        # if Authority.objects.filter(id__in=authority_ids, admins__id=user.id).count() > 0:
        #     return True
        #
        # return self.id == user.id

        return False


if not hasattr(Group, 'type'):
    field = models.PositiveIntegerField(Group, blank=True, default=0, choices=GROUP_WORKING_TYPE_CHOICES)
    field.contribute_to_class(Group, 'type')


# deprecated
class GroupReportType(models.Model):
    report_type = models.ForeignKey('reports.ReportType')
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return self.group.name


# deprecated
class GroupAdministrationArea(models.Model):
    administration_area = models.ForeignKey('reports.AdministrationArea')
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return self.group.name


class UserDevice(MultiDomainMixin, AbstractCommonTrashModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='device')
    android_id = models.CharField(max_length=100, blank=True, default='')
    device_id = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    wifi_mac = models.CharField(max_length=255, blank=True, default='')
    gcm_reg_id = models.CharField(max_length=255, blank=True, default='')
    apns_reg_id = models.CharField(max_length=255, blank=True, default='')


class Configuration(models.Model):
    """
    *@DynamicAttrs*
    """
    system = models.CharField(max_length=100)
    key = models.CharField(max_length=100)
    value = models.TextField()


# deprecated
class NearbyArea(models.Model):
    area = models.OneToOneField('reports.AdministrationArea', related_name='nearby')
    neighbors = models.ManyToManyField('reports.AdministrationArea', related_name='neighbors')

    def __unicode__(self):
        return 'Neighbors around %s' % self.area.name


class CustomPermission(models.Model):
    name = models.CharField(max_length=50)
    codename = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ('codename', )

    def __unicode__(self):
        return self.name


class RoleCustomPermission(models.Model):

    role_custom_permissions = models.ForeignKey('accounts.CustomPermission', related_name=u'Custom Permissions')
    role = models.CharField(max_length=100, choices=USER_STATUS_CHOICES, verbose_name=u'สถานะผู้ใช้', )

    def __unicode__(self):
        return self.role_custom_permissions.name


def user_can_edit_basic_check(user, extra=False):
    if user and user.is_authenticated() and user.is_staff:
        return True

    if user and not user.is_anonymous and user.status not in [USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER]:
        return bool(extra)

    return False


class Authority(DomainMixin):
    """
    *@DynamicAttrs*
    """
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='authority_created_by', null=True, blank=True)

    inherits = models.ManyToManyField('self', related_name='authority_inherits', symmetrical=False, null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='authority_users', null=True, blank=True)
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='authority_admins', null=True, blank=True)

    deep_subscribes = models.ManyToManyField('self', related_name='authority_deep_subscribes', symmetrical=False, null=True, blank=True)

    area = models.MultiPolygonField(srid=4326, null=True, blank=True)
    # denormalize on save
    #administration_areas = models.ManyToManyField('reports.AdministrationArea', related_name='authority_administration_areas', null=True, blank=True)
    #report_types = models.ManyToManyField('reports.ReportType', related_name='authority_report_types', null=True, blank=True)
    #subscribes = models.ManyToManyField('self', related_name='authority_subscribes', symmetrical=False, null=True, blank=True)

    spreadsheet_key = models.TextField(blank=True, null=True)

    group = models.IntegerField(max_length=10, default=0)

    FIELDS_STORES = {'report_types': 'report_type_authority'}
    FIELDS_STORES_SWAP = {'administration_areas': 'area_authority'}

    tags = TaggableManager()

    graph_node = True
    graph_relations = ['inherits', 'deep_subscribes', 'users']

    class Meta:
        unique_together = ("domain", "code")
        ordering = ('name',)


    def __unicode__(self):
        return self.name

    @property
    def administration_areas(self):
        from reports.models import AdministrationArea

        results = self.graph_execute('''
            MATCH (au1:Authority{id: %d, domain_id: %s})<-[:Authority_inherits*0..]-(au2:Authority{domain_id: %s})
            WITH DISTINCT au2
            MATCH(au2)<-[:AdministrationArea_authority]-(ar1:AdministrationArea{domain_id: %s})
            RETURN ar1.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id, self.domain_id, self.domain_id))

        return AdministrationArea.objects.filter(id__in=[area.id for area in results])

    @property
    def report_types(self):
        if not self.id:
            return []

        from reports.models import ReportType

        results = self.graph_execute('''
            MATCH (au1:Authority{id: %d, domain_id: %s})-[:Authority_inherits*0..]->(au2:Authority{domain_id: %s})
            WITH DISTINCT au2
            MATCH(au2)<-[:ReportType_authority]-(rt1:ReportType{domain_id: %s})
            RETURN rt1.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id, self.domain_id, self.domain_id))

        return ReportType.objects.filter(id__in=[report_type.id for report_type in results])

    # Helper method for recursive
    def _inherits_update(self, authority, fields_stores, pass_authority_ids, swap):

        # circular and duplicate check
        if authority.id in pass_authority_ids:
            return
        pass_authority_ids.add(authority.id)

        for field_name, reference_field_name, store in fields_stores:
            store.update(set(getattr(authority, reference_field_name).all()))

        inherit_list = authority.authority_inherits.all() if swap else authority.inherits.all()

        for inherit in inherit_list:
            self._inherits_update(inherit, fields_stores, pass_authority_ids, swap)

    def inherits_update(self, fields_stores, swap):

        fields_stores = copy.deepcopy(fields_stores)  # important clear pointer reference

        self._inherits_update(self, fields_stores, set(), swap)

        for field_name, reference_field_name, store in fields_stores:
            reference_field = getattr(self, field_name)

            #reference_field.clear()
            #reference_field.add(*list(store))

            exists = set(reference_field.all())
            updates = set(store)

            adds = updates - exists
            removes = exists - updates

            for add in adds:
                try:
                    reference_field.add(add)
                    #print 'Add: %s, %s, %s' % (self, field_name, add)
                except IntegrityError:
                    pass
                    #print 'Error: %s, %s, %s' % (self, field_name, add)


            for remove in removes:
                try:
                    reference_field.remove(remove)
                    #print 'Remove: %s, %s, %s' % (self, field_name, remove)

                except IntegrityError:
                    pass
                    #print 'Error: %s, %s, %s' % (self, field_name, remove)



    # Upper and Deeper BFS algorithm
    def _update_stores(self, pass_authority_ids, fields_stores, swap):

        # circular and duplicate check
        if self.id in pass_authority_ids:
            return
        pass_authority_ids.add(self.id)

        # Upper for generate self.report_types
        self.inherits_update(fields_stores, swap)

        # Deeper for update all children report_types
        child_list = self.inherits.all() if swap else self.authority_inherits.all()


        for child in child_list:
            child._update_stores(pass_authority_ids, fields_stores, swap)


    @app.task(filter=task_method, base=DomainTask, bind=True)
    @domain_celery_task
    def update_stores(self, field_names=None):

        invalidate_all()

        # Update all fields and stores
        if not field_names:

            fields_stores = ()
            for field_name, children_related_name in self.FIELDS_STORES.iteritems():
                fields_stores = fields_stores + ((field_name, children_related_name, set()), )

            self._update_stores(set(), fields_stores, False)

            fields_stores = ()
            for field_name, children_related_name in self.FIELDS_STORES_SWAP.iteritems():
                fields_stores = fields_stores + ((field_name, children_related_name, set()), )
            self._update_stores(set(), fields_stores, True)

        else:

            fields_stores = ()
            for field_name in field_names:
                children_related_name = self.FIELDS_STORES.get(field_name)
                if children_related_name:
                    fields_stores = fields_stores + ((field_name, children_related_name, set()), )

            self._update_stores(set(), fields_stores, False)

            fields_stores = ()
            for field_name in field_names:
                children_related_name = self.FIELDS_STORES_SWAP.get(field_name)
                if children_related_name:
                    fields_stores = fields_stores + ((field_name, children_related_name, set()), )

            self._update_stores(set(), fields_stores, True)

        # print 'Success: update_stores %s' % self.name


    @property
    def _base_notification_template_list(self):

        from notifications.models import NotificationTemplate

        allow_id_list = set(self.get_inherits_all()) | set(self.get_subscribes_all())
        allow_id_list.add(self.id)
        return NotificationTemplate.objects.filter(authority__in=allow_id_list).distinct()

    def notification_template_enabled_list(self):
        from notifications.models import NotificationTemplate

        return self._base_notification_template_list.filter(
            (Q(type=NotificationTemplate.TYPE_REPORTER_FEEDBACK) & Q(notice_template__authority=self) & Q(authority=self)) |
            (~Q(type=NotificationTemplate.TYPE_REPORTER_FEEDBACK) & Q(notice_template__authority=self))
        )

    def notification_template_disabled_list(self):
        return self._base_notification_template_list.exclude(notice_template__authority=self)

    def notification_template_cannot_disable_list(self):
        from notifications.models import NotificationTemplate
        return self._base_notification_template_list.filter(type=NotificationTemplate.TYPE_REPORTER_FEEDBACK, notice_template__authority=self).exclude(authority=self)

    def get_parent_name(self):
        parent = self.inherits.all()[:1]
        if parent:
            return parent[0].name
        else:
            return ''

    @property
    def invite(self):
        return self.get_invite()

    def get_invite(self, status=None, trainer_status=None, trainer_authority=None):

        try:
            invite = AuthorityInvite.objects.filter(
                authority=self,
                expired_at__gte=timezone.now(),
                disabled=False,
                status=status,
                trainer_status=trainer_status,
                trainer_authority=trainer_authority

            ).latest('created_at')
        except AuthorityInvite.DoesNotExist:
            invite = AuthorityInvite.objects.create(authority=self, status=status, trainer_status=trainer_status, trainer_authority=trainer_authority)


        return invite

    def renew_invite(self, status=None, trainer_status=None, trainer_authority=None):

        for invite in AuthorityInvite.objects.filter(authority=self, disabled=False, status=status, trainer_status=trainer_status, trainer_authority=trainer_authority):
            invite.disabled = True
            invite.save()

        invite = AuthorityInvite.objects.create(authority=self, status=status, trainer_status=trainer_status, trainer_authority=trainer_authority)


        return invite

    # deprecate
    def invite_code_by_status(self):

        value = {}
        for key, label in USER_STATUS_CHOICES:
            if key:
                invite = self.get_invite(status=key)
                value[key] = invite.code
        return value


    def get_subscribes_all(self):

        results = DomainMixin().graph_execute('''
            MATCH (au1:Authority{id: %d, domain_id: %s})-[:Authority_deep_subscribes*1..1]->(au2:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WHERE NOT (au1:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WITH DISTINCT au3
            RETURN au3.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id))

        return [r.id for r in results]

    def get_subscribers_all(self):

        results = DomainMixin().graph_execute('''
            MATCH (au1:Authority{id: %d, domain_id: %s})-[:Authority_inherits*0..]->(au2:Authority)<-[:Authority_deep_subscribes*1..1]-(au3:Authority)
            WHERE NOT (au2:Authority)-[:Authority_inherits*0..]->(au3:Authority)
            WITH DISTINCT au3
            RETURN au3.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id))

        return [r.id for r in results]

    def get_inherits_all(self, with_obj=False):
        results = DomainMixin().graph_execute('''
            MATCH(au1:Authority{id: %d, domain_id: %s})-[:Authority_inherits*1..]->(au2:Authority{domain_id: %s})
            WITH DISTINCT au2
            RETURN au2.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id, self.domain_id))

        ids = [r.id for r in results]

        if with_obj:
            return Authority.objects.filter(id__in=ids)

        return ids

    def get_children_all(self, with_obj=False):

        results = DomainMixin().graph_execute('''
            MATCH(au1:Authority{id: %d, domain_id: %s})<-[:Authority_inherits*1..]-(au2:Authority{domain_id: %s})
            WITH DISTINCT au2
            RETURN au2.id AS id
            ORDER BY id
        ''' % (self.id, self.domain_id, self.domain_id))

        ids = [r.id for r in results]

        if with_obj:
            return Authority.objects.filter(id__in=ids)

        return ids

    def _get_children_all(self, children):
        for child in self.authority_inherits.all():
            if child not in children:
                children.append(child)
                child._get_children_all(children)

    def get_users_all(self):
        users = set(self.users.filter(domains=self.domain, is_active=True))
        for child in self.get_children_all(with_obj=True):
            print child
            users = users | set(child.users.filter(domains=self.domain, is_active=True))

        return users

    def get_location(self):
        x = []
        y = []
        for area in self.administration_areas.filter(location__isnull=False):
            x.append(float(area.location.x))
            y.append(float(area.location.y))

        if len(x) and len(y):
            return {
                'x': sum(x)/len(x),
                'y': sum(y)/len(y),
            }

        return None

    @app.task(filter=task_method, base=DomainTask, bind=True)
    @domain_celery_task
    def enable_default_reporter_notification_templates(self):
        from notifications.models import NotificationTemplate, NotificationAuthority

        inherits = self.get_inherits_all()
        enable_list = NotificationTemplate.objects.filter(
            type__in=[NotificationTemplate.TYPE_REPORTER_FEEDBACK, NotificationTemplate.TYPE_NOTIFY_FOLLOW_UP],
            notice_template__authority__in=inherits
        )

        for enable in enable_list:
            enabled, created = NotificationAuthority.objects.get_or_create(template=enable, authority=self)

        # print 'Success: enable_default_reporter_notification_templates %s' % self.name

    def save(self, *args, **kwargs):
        is_new = not self.id
        super(Authority, self).save(*args, **kwargs)
        if is_new:
            self.enable_default_reporter_notification_templates()

            if self.created_by:
                self.admins.add(self.created_by)

            #self.update_stores()

        else:
            #self.update_stores.delay()
            pass

    def user_can_edit(self, user):
        return user_can_edit_basic_check(user, self.admins.filter(id=user.id).count() > 0)


def authority_m2m_changed(sender, **kwargs):
    action = kwargs['action']
    instance = kwargs['instance']

    if sender is Authority.inherits.through and action in ['post_add']:
        instance.enable_default_reporter_notification_templates.delay()


    # add admins to users automatically
    elif sender is Authority.admins.through and action in ['post_add']:
        for user in User.objects.filter(id__in=kwargs['pk_set']):
            # print 'add_user %s' % user
            instance.users.add(user)


    # add/remove users to admins automatically
    elif sender is Authority.users.through:
        if action in ['post_remove']:
            for user in instance.admins.filter(id__in=kwargs['pk_set']):
                instance.admins.remove(user)
        elif action in ['pre_clear']:
            instance.admins.clear()

m2m_changed.connect(authority_m2m_changed)


class AuthorityInvite(DomainMixin):
    code = models.CharField(max_length=255, unique=True)
    authority = models.ForeignKey(Authority, related_name='authority_invite_authority')

    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()

    disabled = models.BooleanField(default=False)

    # deprecate
    status = models.CharField(max_length=100, choices=USER_STATUS_CHOICES, blank=True, null=True, verbose_name=u'สถานะ')

    trainer_authority = models.ForeignKey(Authority, blank=True, null=True, related_name='authority_invite_trainer_authority')
    trainer_status = models.CharField(max_length=100, choices=USER_STATUS_CHOICES, blank=True, null=True, verbose_name=u'จากสถานะ')

    @property
    def expired_date_at(self):
        return self.expired_at.strftime("%d/%m/%Y")

    def generate_code(self):
        return '{0:07d}'.format(randint(0, 9999999))

    def save(self, *args, **kwargs):

        if not self.id and not self.code:
            self.code = self.generate_code()

        if not self.expired_at:
            now = timezone.now()
            self.expired_at = now + datetime.timedelta(minutes=settings.MINUTES_PER_DAY * settings.AUTHORITY_INVITE_EXPIRE_DAYS)

        try:
            super(AuthorityInvite, self).save(*args, **kwargs)
        except (IntegrityError, ValidationError):
            self.code = self.generate_code()
            self.save(*args, **kwargs)


# Will delete when migrate data to authority? Yes.
# deprecated
class GroupInvite(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    groups = models.ManyToManyField(Group, related_name='invite_groups', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id and not self.code:
            rand = randint(0, 99999)
            self.code = '{0:05d}'.format(rand)

        if not self.expired:
            now = datetime.datetime.now()
            self.expired = now + datetime.timedelta(days=30)
        super(GroupInvite, self).save(*args, **kwargs)



# deprecated ???
class UserCode(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    code = models.CharField(max_length=255, unique=True)

    is_used = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()

    def __unicode__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.id and not self.code:
            from random import randint
            rand = randint(0, 99999)
            self.code = '{0:05d}'.format(rand)

        if not self.expired:
            now = datetime.datetime.now()
            self.expired = now + datetime.timedelta(days=1)

        super(UserCode, self).save(*args, **kwargs)

