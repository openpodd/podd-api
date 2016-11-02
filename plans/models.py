import json
from django.contrib.gis.measure import D
from django.db import models
from django.forms import model_to_dict
from common.models import DomainMixin
from notifications.models import NotificationTemplate


def area_to_dict(area):
    area = model_to_dict(area)

    if area['location']:
        area['location'] = json.loads(area['location'].json)

    if area['mpoly']:
        area['mpoly'] = None
        #area['mpoly'] = json.loads(area['mpoly'].json)

    return area

def template_to_dict(template):
    template = model_to_dict(template)
    template['template'] = json.loads(template['template'])
    return template


class Plan(DomainMixin):

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, unique=True)

    condition = models.TextField()

    _cal_level_areas = False
    _level_areas = {}

    def __unicode__(self):
        return '%s' % (self.name or self.condition)

    def level_areas(self, area):

        if self._cal_level_areas:
            return self._level_areas

        from reports.models import AdministrationArea

        areas = {}

        prev_distance = 0
        prev_level_areas = set([])

        is_mpoly_valid = area.mpoly and area.location.within(area.mpoly)

        for level in self.levels.all():

            level_areas = AdministrationArea.objects \
                .filter(location__distance_gte=(area.location, D(m=(prev_distance)))) \
                .filter(location__distance_lt=(area.location, D(m=(level.distance))))

            level_areas = set(level_areas)

            if is_mpoly_valid:
                mpoly_level_areas = AdministrationArea.objects \
                    .filter(mpoly__distance_gte=(area.location, D(m=(prev_distance)))) \
                    .filter(mpoly__distance_lt=(area.location, D(m=(level.distance))))

                level_areas |= set(mpoly_level_areas)

            if prev_distance == 0:
                level_areas |= set([area])

            level_areas = level_areas - prev_level_areas


            prev_distance = level.distance
            prev_level_areas = level_areas

            areas[level.code] = list(level_areas)


        self._level_areas = areas
        self._cal_level_areas = True

        return areas

    def dict_level_areas(self, area):
        level_areas = self.level_areas(area)

        dict_level_areas = {}
        for level, areas in level_areas.iteritems():
            dict_level_areas[level] = [area_to_dict(a) for a in areas]

        return dict_level_areas

    def dict_level_authority_ids(self, area):
        level_areas = self.level_areas(area)

        dict_level_authority_ids = {}
        for level, areas in level_areas.iteritems():
            dict_level_authority_ids[level] = list(set([a.authority.id for a in areas if a.authority]))

        return dict_level_authority_ids


class PlanLevel(DomainMixin):

    plan = models.ForeignKey(Plan, related_name='levels')

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)

    distance = models.IntegerField()

    extra_data = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['distance']

    def __unicode__(self):
        return '%s %s' % (self.plan, (self.name or self.code))


class PlanReport(DomainMixin):
    plan = models.ForeignKey(Plan)
    report = models.ForeignKey('reports.Report')

    areas = models.ManyToManyField('reports.AdministrationArea', null=True, blank=True)

    log = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    level_templates = {}

    def save(self, *args, **kwargs):

        from plans.serializers import PlanSerializer
        from reports.serializers import ReportSerializer

        is_new = self.id is None
        area = self.report.administration_area

        if is_new:
            self.log = json.dumps({
                'plan': PlanSerializer(self.plan).data,
                'report': ReportSerializer(self.report).data,
                'level_areas': self.plan.dict_level_areas(area),
                'level_authority_ids': self.plan.dict_level_authority_ids(area),
                'level_templates': {}
            })

        else:
            log = json.loads(self.log)
            if not log.get('level_templates'):
                level_templates = {}
                for level, templates in self.level_templates.iteritems():
                    # print plan_report.level_templates[level]
                    level_templates[level] = [template_to_dict(t) for t in set(templates)]

                self.level_templates = level_templates

                log['level_templates'] = self.level_templates
                self.log = json.dumps(log)


        super(PlanReport, self).save(*args, **kwargs)

        if is_new:
            for level, areas in self.plan.level_areas(area).iteritems():
                self.areas.add(*areas)

    def notify(self, area):

        log = json.loads(self.log)
        level_templates = log.get('level_templates')
        level_areas = log.get('level_areas')

        level_contacts = {}

        accepted_level_templates = {}
        for level, areas in level_areas.iteritems():

            areas_id = [a['id'] for a in areas]
            if area.id in areas_id:
                accepted_level_templates[level] = level_templates[level]
                level_contacts[level] = area.get_contacts()

        for level, templates in accepted_level_templates.iteritems():

            notification_template_accepted_list = [NotificationTemplate(
                id=t['id'],
                template=t['template'],
                description=t['description'],
                type=t['type']
            ) for t in templates]

            sents = {}
            for accepted in notification_template_accepted_list:
                sents[accepted.get_comment_render()] = []

            stamps = []

            self.report._create_notification(
                notification_template_accepted_list,
                [self.report.administration_area.authority],
                sents,
                stamps=stamps,
                inherits_send=True,
                direct_to_list=level_contacts[level]
            )
            self.report.create_comment_notification(sents)


