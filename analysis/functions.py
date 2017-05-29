# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
import datetime
import json
import csv

'''
Output Columns:
 - report.id
 - report.date
 - report.incident_date
 - u.username
 - u.first_name
 - u.last_name
 - a.id
 - a.name [administration_area -> หมู่บ้าน, อบต, สหกรณ์]
 - aa.id
 - aa.name [parent administration_area -> อำเภอ, สหกรณ์]
 - form.species
 - form.disease
 - form.symptom1....N
 - form.sick_count
 - form.death_count
 - form.total_count
 - form.nearby_count
 - follow [0 -> normal, 1 - follow]
 - follow_idx
'''

from django.db import connection
cur = connection.cursor()

# connection_str = 'dbname=podd user=podd password=podd port=5432 host=localhost'
# conn = psycopg2.connect(connection_str)
# cur = conn.cursor()


def build_sql(date_start=None, date_end=None):

    date_start = date_start or '2015-01-01'
    date_end = date_end or datetime.datetime.now().strftime('%Y-%m-%d')

    sql = ('''
    select
      t.name,                     /* 0 */
      r.date,                     /* 1 */
      r.incident_date,
      u.username,				  /* 3 */
      u.first_name,
      u.last_name,                /* 5 */
      a.id as sub_district_id,
      a.name as sub_district,
      aa.id as district_id,       /* 8 */
      aa.name as district,        /* 9 */
      r.form_data,                /* 10 */
      r.parent_id,
      r."id"					  /* 12 */
    from reports_report r,
     reports_reporttype t,
    accounts_user u,
    reports_administrationarea a,
    reports_administrationarea aa
    where r.type_id = t."id"
    and u.id = r.created_by_id
    and r.administration_area_id = a.id
    and r.date >= '{0}'
    and r.date < '{1}'
    and a.lft between aa.lft and aa.rgt
    and (r.test_flag is null or r.test_flag = false)     /*  ไม่ใช่รายงานทดสอบ */
    and r.is_public = false     /*  ไม่ใช่ public report */
    and r.domain_id = 1         /*  podd domain */
    and r.type_id = 2           /*  สัตว์ป่วยตาย */
    and a.tree_id = aa.tree_id
    and aa.id != 112			/* test area not include */
    and a.id != aa.id
    and u.username like 'podd%'
    and r.negative = true
    order by r.id
    ''').format(date_start, date_end)

    cur.execute(sql)


def populate_symptom_map(symptoms):

    symptom_map = {}

    from reports.models import ReportType
    rt = ReportType.objects.get(id=2)

    from analysis.models import Word
    words = {}
    for word in Word.objects.all():
        words[word.th_word] = word.en_word

    import json
    form = json.loads(rt.form_definition)
    q = form['questions']

    for _q in q:
        if 'symptom' in _q['name']:
            if _q.has_key('items'):
                items = _q['items']
                for item in items:
                    item['text'] = item['text'].replace(' ', '')
                    try:
                        key = words[item['text']]
                    except KeyError:
                        key = item['text']
                    if not symptom_map.has_key(item['text']):
                        symptom_map[key] = 1
                    else:
                        symptom_map[key] += 1
    return symptom_map


def populate_symptom_map_from_report(symptom_map, symptoms):
    for symptom in symptoms:
        if not symptom_map.has_key(symptom):
            symptom_map[symptom] = 1
        else:
            symptom_map[symptom] = +1

    return symptom_map


def fetch_column(row):
    return {
        'id': row[12],
        'parent_id': row[11],
        'name': row[0],
        'date': row[1],
        'incident_date': row[2],
        'username': row[3],
        'first_name': row[4],
        'last_name': row[5],
        'sub_district_id': row[6],
        'sub_district_name': row[7],
        'district_id': row[8],
        'district_name': row[9],
        'form': json.loads((row[10]))
    }


class Report:
    def __init__(self, words, params):
        self.params = params
        self.follow_list = []
        self.has_follow = False
        self.follow = False
        self.words = words

    def add_follow(self, report):
        self.follow_list.append(report)

    def symptoms(self):
        words = self.words
        if self.form.has_key('symptom'):
            tmp_symptoms = self.form['symptom']
            tmp_symptoms = tmp_symptoms.split(',')
            symptoms = []
            for symptom in tmp_symptoms:
                symptom = symptom.replace(' ', '')
                try:
                    symptoms.append(words[symptom])
                except KeyError:
                    symptoms.append(symptom)
            return symptoms
        return []

    def __getattr__(self, name):
        if self.params.has_key(name):
            return self.params[name]
        if self.params['form'].has_key(name):
            return self.params['form'][name]
        # print "error on id = %s" % (self.id,)
        raise AttributeError(name)

    @classmethod
    def to_header(cls):
        return [
            'report_id',
            'report_date',
            'report_incident_date',
            'username',
            'first_name',
            'last_name',
            'sub_district_id',
            'sub_district_name',
            'district_id',
            'district_name',
            'species',
            'disease',
            'sick_count',
            'death_count',
            'total_count',
            'nearby_count',
            'follow_flag',
            'follow_id',
            'follow_idx',
        ]

    def to_array(self, follow_format=False, follow_idx = 0):
        return [
            self.id,
            self.date.isoformat(),
            self.incident_date.isoformat(),
            self.username,
            self.first_name.encode('utf-8'),
            self.last_name.encode('utf-8'),
            self.sub_district_id,
            self.sub_district_name.encode('utf-8'),
            self.district_id,
            self.district_name.encode('utf-8'),
            self.animalType.encode('utf-8'),
            self.disease.encode('utf-8') if self.form.has_key('disease') else 'NA',
            self.sickCount,
            self.deathCount,
            self.totalCount,
            self.nearByCount,
            1 if follow_format else 0,
            self.parent_id if follow_format else self.id,
            follow_idx if follow_format else 0
        ]


def fetch_report(date_start=None, date_end=None):

    from reports.models import ReportType
    rt = ReportType.objects.get(id=2)

    from analysis.models import Word
    words = {}
    for word in Word.objects.all():
        words[word.th_word] = word.en_word

    import json
    form = json.loads(rt.form_definition)
    q = form['questions']

    symptom_map = {}

    report_map = {}
    reports = []
    build_sql(date_start, date_end)
    for row in cur:
        report = Report(words, fetch_column(row))
        report_map[report.id] = report
        symptom_map = populate_symptom_map(report.symptoms())
        symptom_map = populate_symptom_map_from_report(symptom_map, report.symptoms())
        parent_id = report.params['parent_id']
        if parent_id and report_map.has_key(parent_id):
            parent_report = report_map[parent_id]
            if parent_report:
                report.follow = True
                parent_report.has_follow = True
                parent_report.add_follow(report)
                # print "add follow report: %s to %s " % (report.id, parent_id)
        else:
            reports.append(report)
    return reports, symptom_map


def dump_symptom_header(symptom_map):
    return [key.encode('utf-8') for key in symptom_map.keys()]


def dump_symptom_table(symptom_map, symptoms):
    results = []
    for key in symptom_map.keys():
        results.append(1 if key in symptoms else 0)
    return results


def dump_csv(reports, symptom_map):
    with open('/tmp/sick_death.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(Report.to_header() + dump_symptom_header(symptom_map))
        for report in reports:
            try:
                writer.writerow(report.to_array() + dump_symptom_table(symptom_map, report.symptoms()))
                if len(report.follow_list) > 0:
                    cnt = 1
                    for follow in report.follow_list:
                        writer.writerow(follow.to_array(follow_format=True, follow_idx=cnt) + dump_symptom_table(symptom_map, follow.symptoms()))
                        cnt += 1
            except AttributeError as e:
                print "error with e %s" % (e,)


def export():
    reports, symptom_map = fetch_report()
    print 'total count = %d' % (len(reports),)
    # for (k,v) in symptom_map.items():
    #    print "%s" % (k)
    dump_csv(reports, symptom_map)
