# -*- encoding: utf-8 -*-

import datetime
import json
import redis

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from django_redis import get_redis_connection

from accounts.models import Configuration, User
from common.constants import (GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_REPORT_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_ALERT_CASE_ADMINSTRATION_AREA)

from common.constants import USER_STATUS_VOLUNTEER, USER_STATUS_ADDITION_VOLUNTEER
from common.functions import (filter_permitted_administration_areas_and_descendants, has_permission_on_administration_area,
    get_administration_area_and_descendants, filter_permitted_report_types, filter_permitted_administration_areas_and_descendants_by_authorities,
    filter_permitted_report_types_by_authorities)
from reports.models import Report, AdministrationArea, ReportType
from summary.objects import ReporterDetail, ComputeGrade


def summary_by_show_user_detail(user, month=None, force=False, tz=7):
    try:
        month_start = datetime.datetime.strptime(month, '%m/%Y') + relativedelta(hours=tz)
        month_end = month_start + relativedelta(months=+1, days=-1) + relativedelta(hours=tz)
    except:
        return {}
    else:

        try:
            time_ranges = json.loads(Configuration.objects.get(system='web.summary.person', key='time_ranges').value)
        except:
            time_ranges = [
                {'startTime': 0.0, 'endTime': 6.0},
                {'startTime': 6.0, 'endTime': 12.0},
                {'startTime': 12.0, 'endTime': 18.0},
                {'startTime': 18.0, 'endTime': 24.0},
            ]

        report_types = ReportType.objects.all()
        reporter = ReporterDetail(user.id, user.get_full_name(), user.status,
                                  user.thumbnail_avatar_url, user.get_authority(), report_types, time_ranges)

        reports = Report.objects.filter(Q(created_by=user))
        reports = reports.filter(date__range=(month_start + datetime.timedelta(hours=tz),
                                              month_end + datetime.timedelta(hours=tz)))
        reports = reports.exclude(test_flag=True).values('type', 'form_data', 'date', 'created_by', 'administration_area', 'negative')

        for report in reports:
            try:
                form_data = json.loads(report['form_data'])
                animal_type = {}
                if form_data.get('animalType'):
                    animal_type = {
                        'name': form_data.get('animalType'),
                        'sick': int(form_data.get('sickCount')) if form_data.get('sickCount') else 0,
                        'death': int(form_data.get('deathCount')) if form_data.get('deathCount') else 0,
                        'total': int(form_data.get('totalCount')) if form_data.get('totalCount') else 0,
                        'nearBy': int(form_data.get('nearByCount')) if form_data.get('nearByCount') else 0
                    }

                created_by_hours = report['date'].hour % 24
                report_date = (report['date']).strftime('%d-%m-%Y')
                reporter.put_report(
                    type=report['type'],
                    report_animal_type=animal_type,
                    report_negative=report['negative'],
                    report_date=report_date,
                    created_by_hour=created_by_hours
                )
            except KeyError:
                pass

        grade = 'A' if len(reporter.dateReports) > 20 else 'B' if len(reporter.dateReports) > 10 else 'C'
        setattr(reporter, 'grade', grade)
        return json.dumps(reporter, default=lambda o: o.__dict__)


def get_elastic_search_body(user, date_gte='2014-12-01', date_lt='now', subscribes=False, authority_id=None):

    if not user.is_staff:
        permitted_report_types = filter_permitted_report_types(user, subscribes=subscribes)
        permitted_administration_areas = filter_permitted_administration_areas_and_descendants(user,
                                                                                               ids_only=True,
                                                                                               subscribes=subscribes)
    else:
        permitted_report_types = list(ReportType.objects.values_list('id', flat=True))
        permitted_administration_areas = list(AdministrationArea.objects.values_list('id', flat=True))

    if authority_id:
        permitted_report_types = filter_permitted_report_types_by_authorities(user.domain_id, authority_id, subscribes=subscribes)
        permitted_administration_areas = filter_permitted_administration_areas_and_descendants_by_authorities(user.domain_id,
                                                                                                              authority_id,
                                                                                                              ids_only=True,
                                                                                                              subscribes=subscribes)
    elastic_search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                              {"match": {"testFlag": False}},
                            ]
                          }
                    }, {
                        "bool": {
                            "must": {
                                "terms": {
                                    "type": permitted_report_types,
                                    "minimum_should_match": 1
                                }
                            }
                        }
                    }, {
                        "bool": {
                            "must": {
                                "terms": {
                                    "administrationArea": permitted_administration_areas,
                                    "minimum_should_match": 1
                                }
                            }
                        }
                    },
                    {
                        "constant_score": {
                            "filter": {
                                "missing": {"field": "parent"}
                            }
                        }
                    },
                    {
                        "range": {
                            "date": {
                                "gte": date_gte,
                                "lt": date_lt,
                                "boost": 2.0
                            }
                        }
                    }
                ]
            }
        },
        "filter": {},
        "aggregations": {
            "reportType": {
                "terms": {
                    "field": "type",
                    "min_doc_count": 0,
                    "size": 0
                }
            },
        }
    }
    return elastic_search_body