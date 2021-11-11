# -*- coding: utf-8 -*-
import json
from dateutil.parser import parse
import pandas
import pytz

tz = pytz.timezone('Asia/Bangkok')

def fetch_report_type_id(conn, code, domain_id=1):
    cur = conn.cursor()
    cur.execute("select id from reports_reporttype where code = %s and domain_id = %s", (code, domain_id,))
    (report_type_id,) = cur.fetchone()
    cur.close()
    return report_type_id


def fetch_reports(conn, report_type_id, date_begin, date_end, authority_ids, domain_id=1):
    find_report_query = """
    select id, 
           parent_id as group_id,
           original_form_data as form_data, 
           date,
           ST_X(report_location::geometry) as longitude,
           ST_Y(report_location::geometry) as latitude 
          from reports_report
          where type_id = %s
          and date between %s and %s
          and (test_flag is null or test_flag = FALSE)
          and negative = TRUE 
          and domain_id = %s
          and administration_area_id in (
            select id from reports_administrationarea 
            where authority_id = any(%s)
          )
          order by id

    """
    cur = conn.cursor()
    cur.execute(find_report_query, (report_type_id, date_begin, date_end, domain_id, authority_ids))
    rows = cur.fetchall()
    cur.close()

    results = []
    for row in rows:
        (report_id, group_id, form_data_str, date, longitude, latitude) = row
        form_data = json.loads(form_data_str)
        results.append({
            'report_id': report_id,
            'group_id': group_id,
            'date': date,
            'form_data': form_data,
            'longitude': longitude,
            'latitude': latitude,
        })

    return results

def fetch_form_data(form_data):
    def get_value(key):
        return form_data[key] if key in form_data else None

    name = get_value('name')
    gender = get_value('gender')
    age = get_value('age')
    village_no = get_value('village_no')
    village = get_value('village')
    tumbols = get_value('tumbols')
    amphurs = get_value('amphurs')
    arrival_date_village = get_value('arrival_date_village')
    mobile_phone = get_value('mobile_phone')
    risk_factor = get_value('risk_factor')
    symptom_check = get_value('symptom_check')
    symptom_covid = get_value('symptom_covid')
    total_times = get_value('total_times')
    activity_other = get_value('activity_other')

    return {
        'name': name,
        'gender': gender,
        'age': age,
        'village_no': village_no,
        'village': village,
        'tumbols': tumbols,
        'amphurs': amphurs,
        'arrival_date_village': arrival_date_village,
        'mobile_phone': mobile_phone,
        'risk_factor': risk_factor,
        'symptom_check': symptom_check,
        'symptom_covid': symptom_covid,
        'total_times': total_times,
        'activity_other': activity_other
    }


def fetch_data(conn,
               date_begin,
               date_end,
               authority_ids,
               domain_id,
               type_id, ):
    results = []
    main_data = fetch_reports(conn, type_id, date_begin, date_end, authority_ids, domain_id)
    for row in main_data:
        form_data = row['form_data']
        record = fetch_form_data(form_data)
        record['report_id'] = row['report_id']
        record['group_id'] = row['group_id']
        record['date'] = row['date']
        record['longitude'] = row['longitude']
        record['latitude'] = row['latitude']
        results.append(record)
    return results


def tabular(main_data):
    for row in main_data:
        # pass I: sort all follow up report
        row['followup'].sort(key=lambda r: r['date'])
        d0 = row['date'].replace(hour=0, minute=0, second=0, microsecond=0)
        # create 14 slot
        for i in range(1, 15):
            row['%02d' % (i,)] = ''
        remaining = 14
        # put follow up report into slot
        for report in row['followup']:
            report_date = report['date'].replace(hour=0, minute=0, second=0, microsecond=0)
            delta = report_date - d0
            diff_day = delta.days
            if 0 < diff_day <= 14:
                remaining = remaining - 1
                row['%02d' % (diff_day,)] = 'X' if not report['symptom_covid'] else report['symptom_covid']
        row['remaining'] = remaining


def join(main_data, follow_data):
    results = []
    id_map = {}
    for row in main_data:
        id_map[row['report_id']] = row
        row['group_id'] = row['report_id']
        row['followup'] = []
        results.append(row)
    for row in follow_data:
        group_id = row['group_id']
        if group_id in id_map:
            origin = id_map[group_id]
            origin['followup'].append(row)
    return results


def flat(main_data):
    results = []
    for row in main_data:
        results.append(row)
        for follow in row['followup']:
            tmp = follow.copy()
            for key in ['name', 'gender', 'age', 'village', 'village_no', 'tumbols', 'amphurs', 'arrival_date_village', 'mobile_phone']:
                tmp[key] = row[key]
            results.append(tmp)
    return results


def run(params, conn, outputfile):
    """
    create spreadsheet fill with mers line listing
    :param dict that contain
        date_begin: string format 'yyyy-mm-dd'
        date_end: string format 'yyyy-mm-dd'
        domain_id: int
        authority_ids: array of authority id
    :param conn database connection
    :param outputfile string filename with fullpath
    :return:
    """
    date_begin = parse(params['date_begin'] + ' 00:00:00 +0700')
    date_end = parse(params['date_end'] + ' 23:59:59 +0700')
    domain_id = params['domain_id']
    authority_ids = params['authority_ids']

    covid_report_type_id = fetch_report_type_id(conn, 'surveillance-covid-19', domain_id)
    main_data = fetch_data(conn, date_begin, date_end, authority_ids, domain_id, covid_report_type_id)

    covid_report_type_id = fetch_report_type_id(conn, 'surveillance-covid-19-followup', domain_id)
    follow_data = fetch_data(conn, date_begin, date_end, authority_ids, domain_id, covid_report_type_id)

    line_list = join(main_data, follow_data)
    tabular(line_list)

    if len(line_list) == 0:
        return False

    df = pandas.DataFrame(line_list)
    df['date'] = df['date'].dt.tz_convert(tz)
    df['date'] = df['date'].dt.strftime('%d/%m/%Y %H:%M')
    writer = pandas.ExcelWriter(outputfile)
    df.to_excel(writer, 'covid-19', columns=['report_id', 'name', 'gender', 'age',
                                             'village_no', 'village', 'tumbols', 'amphurs',
                                             'arrival_date_village', 'mobile_phone',
                                             'risk_factor', 'symptom_check', 'symptom_covid',
                                             'date', 'latitude', 'longitude',
                                             '01', '02', '03', '04', '05', '06',
                                             '07', '08', '09', '10', '11', '12', '13', '14'], index=False)
    ldf = pandas.DataFrame(flat(main_data))
    ldf['date'] = ldf['date'].dt.tz_convert(tz)
    ldf.sort_values(by=['date'], inplace=True)
    ldf['date'] = ldf['date'].dt.strftime('%d/%m/%Y %H:%M')

    def is_followup(row):
        return row['report_id'] != row['group_id']

    ldf['followup'] = ldf.apply(is_followup, axis=1)
    ldf.to_excel(writer,
                 'all',
                 columns=['report_id', 'group_id', 'followup', 'name', 'gender', 'age',
                          'village_no', 'village', 'tumbols', 'amphurs',
                          'arrival_date_village', 'mobile_phone',
                          'risk_factor', 'symptom_check', 'symptom_covid',
                          'total_times', 'activity_other',
                          'date', 'latitude', 'longitude'],
                 index=False)
    writer.save()
    return True
