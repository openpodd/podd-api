# -*- encoding: utf-8 -*-

import json
import re

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.template import Template, Context
from py2neo import Graph, Record
from py2neo.packages.httpstream import SocketError
import requests
import uuid
import copy
# import signal
import unicodecsv as csv
from uuid import uuid1
import pika

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from asteval import Interpreter


from common.constants import (GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
    GROUP_WORKING_TYPE_REPORT_TYPE, PRIORITY_IGNORE, PRIORITY_OK, PRIORITY_CONTACT, PRIORITY_FOLLOW, PRIORITY_CASE)
from common.pub_tasks import publish

from accounts.models import Configuration


def filter_permitted_administration_areas_and_descendants(user, ids_only=False, subscribes=False, graph_fields_only=False):
    authority_ids = user.authority_users.values_list('id', flat=True)
    authority_ids_string = ','.join(map(str, authority_ids))

    return filter_permitted_administration_areas_and_descendants_by_authorities(user.domain_id, authority_ids_string, ids_only, subscribes, graph_fields_only)


def filter_permitted_administration_areas_and_descendants_by_authorities(domain_id, authority_ids_string, ids_only=False, subscribes=False, graph_fields_only=False):
    from common.models import DomainMixin
    from reports.models import AdministrationArea

    query = '''
        MATCH (au1:Authority{domain_id: %s})<-[:Authority_inherits*0..]-(au2:Authority{domain_id: %s})
        WHERE au1.id IN [%s]
        WITH DISTINCT au1, au2
        MATCH(au2)<-[:AdministrationArea_authority]-(ar1:AdministrationArea{domain_id: %s})
        RETURN ar1.id AS id
    ''' % (domain_id, domain_id, authority_ids_string, domain_id)


    if graph_fields_only:
        query = query + ', ar1.name AS name, ar1.address AS address, ar1.location AS location'

    if subscribes:

        query = query + '''
            UNION
            MATCH (au1:Authority{domain_id: %s})-[:Authority_deep_subscribes*1..1]->(au2:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WHERE au1.id IN [%s]
            WITH DISTINCT au2, au3
            MATCH (au3)<-[:AdministrationArea_authority]-(ar1:AdministrationArea)
            RETURN ar1.id AS id
        ''' % (domain_id, authority_ids_string)

        if graph_fields_only:
            query = query + ', ar1.name AS name, ar1.address AS address, ar1.location AS location'


    results = DomainMixin().graph_execute(query)

    if graph_fields_only:
        return results

    area_ids = [area.id for area in results]
    if ids_only:
        return area_ids

    return AdministrationArea.objects.filter(id__in=area_ids).order_by('name')


def filter_permitted_report_types(user, subscribes=False):
    from reports.models import ReportType

    if user.is_staff:
        return ReportType.objects.values_list('id', flat=True)

    authority_ids = user.authority_users.values_list('id', flat=True)
    authority_ids_string = ','.join(map(str, authority_ids))
    return filter_permitted_report_types_by_authorities(user.domain_id, authority_ids_string, subscribes)


def filter_permitted_report_types_by_authorities(domain_id, authority_ids_string, subscribes=False):
    from common.models import DomainMixin

    query = '''
        MATCH (au1:Authority{domain_id: %s})-[:Authority_inherits*0..]->(au2:Authority{domain_id: %s})
        WHERE au1.id IN [%s]
        WITH DISTINCT au1, au2
        MATCH(au2)<-[:ReportType_authority]-(rt1:ReportType{domain_id: %s})
        RETURN rt1.id AS id
    ''' % (domain_id, domain_id, authority_ids_string, domain_id)

    if subscribes:
        query = query + '''
            UNION
            MATCH (au1:Authority{domain_id: %s})-[:Authority_deep_subscribes*1..1]->(au2:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WHERE au1.id IN [%s]
            WITH DISTINCT au2, au3
            MATCH (au3)<-[:ReportType_authority]-(rt2:ReportType{domain_id: %s})
            RETURN rt2.id AS id
        ''' % (domain_id, authority_ids_string, domain_id)
    results = DomainMixin().graph_execute(query)

    allowed_report_type_ids = [report_type.id for report_type in results]
    allowed_report_type_ids.append(0)
    return allowed_report_type_ids


def has_permission_on_report_type(user, report_type):
    return user.is_staff or report_type.id in filter_permitted_report_types(user)


def has_permission_on_administration_area(user, administration_area, subscribes=False):
    return user.is_staff or administration_area.id in filter_permitted_administration_areas_and_descendants(user, subscribes=subscribes, ids_only=True)


def filter_permitted_users(user, subscribes=False, status=None):
    authority_ids = user.authority_users.values_list('id', flat=True)
    authority_ids_string = ','.join(map(str, authority_ids))
    return filter_permitted_users_by_authorities(user.domain_id, authority_ids_string, subscribes, status)


def filter_permitted_users_by_authorities(domain_id, authority_ids_string, subscribes=False, status=None):
    from common.models import DomainMixin

    query_status = ''
    if status:
        query_status = 'WHERE u2.status IN [%s]' % status

    query = '''
        MATCH (au1:Authority{domain_id: %s})<-[:Authority_inherits*0..]-(au2:Authority{domain_id: %s})
        WHERE au1.id IN [%s]
        WITH DISTINCT au2
        MATCH (au2)-[:Authority_users]->(u2:User{domain_id: %s})
        %s
        WITH DISTINCT u2
        RETURN u2.id AS id
    ''' % (domain_id, domain_id, authority_ids_string, domain_id, query_status)

    if subscribes:
        query_status = ''
        if status:
            query_status = 'WHERE u3.status IN [%s]' % status
        query = query + '''
            UNION
            MATCH (au1:Authority{domain_id: %s})-[:Authority_deep_subscribes*1..1]->(au2:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WHERE au1.id IN [%s]
            WITH DISTINCT au2, au3
            MATCH (au3)-[:Authority_users]->(u3:User{domain_id: %s})
            %s
            WITH DISTINCT u3
            RETURN u3.id AS id
        ''' % (domain_id, authority_ids_string, domain_id, query_status)

    results = DomainMixin().graph_execute(query)
    return [u.id for u in results]


def filter_permitted_authority(user, subscribes=False):

    authority_ids = user.authority_users.values_list('id', flat=True)
    authority_ids_string = ','.join(map(str, authority_ids))
    return filter_permitted_authority_by_authorities(user.domain_id, authority_ids_string, subscribes)


def filter_permitted_authority_by_authorities(domain_id, authority_ids_string, subscribes=False):
    from common.models import DomainMixin

    query = '''
        MATCH (au1:Authority{domain_id: %s})<-[:Authority_inherits*0..]-(au2:Authority{domain_id: %s})
        WHERE au1.id IN [%s]
        WITH DISTINCT au2
        RETURN au2.id AS id
    ''' % (domain_id, domain_id, authority_ids_string)

    if subscribes:
        query = query + '''
            UNION
            MATCH (au1:Authority{domain_id: %s})-[:Authority_deep_subscribes*1..1]->(au2:Authority)<-[:Authority_inherits*0..]-(au3:Authority)
            WHERE au1.id IN [%s]
            WITH DISTINCT au2, au3
            RETURN au3.id AS id
        ''' % (domain_id, authority_ids_string)

    results = DomainMixin().graph_execute(query)
    return [u.id for u in results]


#check permission area_in_authority
def has_permission_area_in_authorities(administration_area, authorities):
    from accounts.models import Authority
    ids = ','.join(str(v) for v in authorities.values_list('id', flat=True))
    results = Authority().graph_execute('''
        MATCH (au1:Authority{domain_id: %s})<-[:Authority_inherits*0..]-(au2:Authority{domain_id: %s})
        WHERE au1.id in [%s]
        WITH DISTINCT au2
        MATCH(au2)<-[:AdministrationArea_authority]-(ar1:AdministrationArea{id: %d, domain_id: %s})
        RETURN ar1.id AS id
        ORDER BY id
    ''' % (administration_area.domain_id, administration_area.domain_id, ids, administration_area.id, administration_area.domain_id))
    return len(results) > 0


# deprecate
def get_administration_area_and_ancestors_ids(area):
    area_ids = [area.id]

    ancestors = area.get_ancestors()
    area_ids.extend(ancestors.values_list('id', flat=True))
    return area_ids


# deprecate
def get_administration_area_and_descendants(areas):
    area_ids = []
    for area in areas:
        area_ids.append(area.id)
        area_ids.extend(area.get_descendants().values_list('id', flat=True))

    from reports.models import AdministrationArea
    return AdministrationArea.objects.filter(id__in=area_ids).order_by('name')


def upload_to_s3(file):        
    from accounts.models import Configuration

    try:
        s3_api_key = Configuration.objects.get(system='s3.server.configuration', key='AWS_ACCESS_KEY_ID')
        s3_secret_key = Configuration.objects.get(system='s3.server.configuration', key='AWS_SECRET_ACCESS_KEY')
        s3_bucket_key = Configuration.objects.get(system='s3.server.configuration', key='BUCKET_KEY')
    except Configuration.DoesNotExist:
        return False

    conn = S3Connection(s3_api_key.value, s3_secret_key.value)
    bucket = conn.get_bucket(s3_bucket_key.value)

    def check_upload_to_s3(sent, filename):
        key = bucket.lookup(filename)
        if key and sent == key.size:
            return True
        return False

    file_key = str(uuid.uuid4())

    ########### Upload file ###########
    key = Key(bucket)
    key.key = file_key
    key.set_metadata('Content-Disposition', 'attachment;filename="%s"' % file.name)
    key.set_contents_from_file(file)
    key.set_acl('public-read')

    ########### Check upload file success ###########
    sent = file.size
    success = check_upload_to_s3(sent, file_key)

    if success:
        return key.generate_url(expires_in=0, query_auth=False)
    return None


# https://gist.github.com/sigilioso/2957026
def resize_and_crop(img_path, modified_path, size, crop_type='middle'):
    """
    Resize and crop an image to fit the specified size.

    args:
    img_path: path for the image to resize.
    modified_path: path to store the modified image.
    size: `(width, height)` tuple.
    crop_type: can be 'top', 'middle' or 'bottom', depending on this
    value, the image will cropped getting the 'top/left', 'middle' or
    'bottom/right' of the image to fit the size.
    raises:
    Exception: if can not open the file in img_path of there is problems
    to save the image.
    ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))),
            Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
                int(round((img.size[1] + size[1]) / 2)))
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else :
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]),
            Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = (int(round((img.size[0] - size[0]) / 2)), 0,
                int(round((img.size[0] + size[0]) / 2)), img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else :
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    else :
        img = img.resize((size[0], size[1]),
            Image.ANTIALIAS)
    # If the scale is the same, we do not need to crop

    img.save(modified_path)


def get_data_from_csv(file_path):
    data = []
    lines = csv.reader(open(file_path, 'rb'))
    headers = []
    is_read_header = False
    for line in lines:
        if not is_read_header:
            for col in line:
                headers.append(col)
            is_read_header = True
            continue

        d = {}
        col = 0
        for header in headers:
            d[header] = line[col]
            col = col + 1
        data.append(d)
    return data


def get_exif_data(image):
    """
    Returns a dictionary from the exif data of an PIL Image item. Also converts
    the GPS Tags

    @see: https://gist.github.com/erans/983821
    """
    exif_data = {}

    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
    except AttributeError:
        pass

    return exif_data


def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to
    degress in float format
    """
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided
    exif_data (obtained through get_exif_data above)
    """
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

    return lat, lon


def publish_gcm_message(gcm_reg_id, message, message_type, notification_id=None, report_id=None, badge=None):
    from accounts.models import Configuration
    
    try:
        gcm_api_key = Configuration.objects.get(system='android.server.push_notification', key='GCM_API_KEY')
    except Configuration.DoesNotExist:
        return

    if settings.NOTIFICATION_DISABLED:
        print '------ GCM PARAMS ------'
        print '  ---- GCMAPIKey:', gcm_api_key.value
        print '  ---- androidRegistrationIds:', gcm_reg_id
        # print '  ---- message:', message
        print '  ---- id:', notification_id
        print '------ /GCM PARAMS -----'
    else:
        publish('news:new', {
            'GCMAPIKey': gcm_api_key.value,
            'androidRegistrationIds': gcm_reg_id,
            'type': message_type,
            'message': message,
            'id': notification_id,
            'reportId': report_id,
            'badge': badge
        })


def publish_apns_message(apns_reg_id, message, notification_id=None, report_id=None, badge=None):
    from accounts.models import Configuration

    if settings.NOTIFICATION_DISABLED:
        print '------ APNS PARAMS ------'
        print '  ---- apnsRegistrationIds:', apns_reg_id
        # print '  ---- message:', message
        print '  ---- id:', notification_id
        print '------ /APNS PARAMS -----'
    else:
        publish('news:new', {
            'apnsRegistrationIds': apns_reg_id,
            'message': message,
            'id': notification_id,
            'reportId': report_id,
            'badge': badge
        })


def publish_sms_message(message, telephones):

    if settings.TESTING:
        return

    from accounts.models import Configuration

    try:
        URL = Configuration.objects.get(system='web.sms.configuration', key='URL').value
        username = Configuration.objects.get(system='web.sms.configuration', key='username').value
        password = Configuration.objects.get(system='web.sms.configuration', key='password').value
        sender = Configuration.objects.get(system='web.sms.configuration', key='sender').value

        message_type = Configuration.objects.get(system='web.sms.configuration', key='message_type').value
        country_code = Configuration.objects.get(system='web.sms.configuration', key='country_code').value
        encoding = Configuration.objects.get(system='web.sms.configuration', key='encoding').value
    except Configuration.DoesNotExist:
        return

    try:
        telephone_length = Configuration.objects.get(system='web.sms.configuration', key='validate_telephone_length').value
    except Configuration.DoesNotExist:
        telephone_length = 10

    send_telephones = ''
    for telephone in telephones:
        if len(telephone.replace('-','')) == telephone_length:
            telephone = '%s%s' % (country_code , telephone.replace('-', '').split('0', 1)[1])
            send_telephones = '%s;%s' % (telephone, send_telephones)

    message = message.encode(encoding)
    params = {
        'Sender': sender,
        'Msnlist': send_telephones,
        'MsgType': message_type,
        'Msg': message,
        'User': username,
        'Password': password
    }
    # print message
    
    if settings.NOTIFICATION_DISABLED:
        print '------ SMS PARAMS ------'
        print params
        print '------ /SMS PARAMS -----'
    else:
        r = requests.post(URL, params=params)
        if "success" not in r.text:
            print r.text
        return r


def make_hash(o):

    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """

    if isinstance(o, (set, tuple, list)):

        return tuple([make_hash(e) for e in o])

    elif not isinstance(o, dict):

        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)

    return hash(tuple(frozenset(sorted(new_o.items()))))


def publish_into_rabbitmq(exchange, exchange_type, routing_key, data):
    pass
    # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    # channel = connection.channel()

    # channel.exchange_declare(exchange=exchange, type=exchange_type)

    # channel.basic_publish(exchange=exchange,
    #                       routing_key=routing_key,
    #                       body=json.dumps(data))

    # connection.close()


def _uuid(url=None):

    _ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    # If no URL is given, generate a random UUID.
    if url is None:
        unique_id = uuid.uuid4().int
    else:
        unique_id = uuid.uuid3(uuid.NAMESPACE_URL, url).int

    alphabet_length = len(_ALPHABET)
    output = []
    while unique_id > 0:
        digit = unique_id % alphabet_length
        output.append(_ALPHABET[digit])
        unique_id = int(unique_id / alphabet_length)
    return "".join(output)


def generate_key(number, prefix=''):
    prefix = prefix and ('%s-' % prefix)
    return '%s%s-%s' % (prefix, urlsafe_base64_encode(force_bytes(number)), _uuid(number))


def decode_generate_key(key):
    try:
        key = key.split('-')[0]
        return urlsafe_base64_decode(key)
    except (ValueError, UnicodeDecodeError, TypeError):
        return None


def generate_username(id):
    return "podd.{0:05d}".format(id) 


def put_data_to_spreadsheet(spreadsheet_key, data):
    if settings.NOTIFICATION_DISABLED:
        return

    if not spreadsheet_key:
        return

    from accounts.models import Configuration

    try:
        client_email = Configuration.objects.get(system='web.spreadsheet.configuration', key='client_email').value
        key = Configuration.objects.get(system='web.spreadsheet.configuration', key='key').value
    except Configuration.DoesNotExist:
        return
    else:
        from oauth2client.client import SignedJwtAssertionCredentials

        json_key = json.loads(key)
        scope = ['https://spreadsheets.google.com/feeds']

        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

        from httplib2 import Http
        http_auth = credentials.authorize(Http())
         
        from apiclient.discovery import build
        service = build('drive', 'v2', http=http_auth)
         
        from gdata.spreadsheet.service import SpreadsheetsService
        sheets = SpreadsheetsService()
        sheets.additional_headers = {'Authorization': 'Bearer %s' % http_auth.request.credentials.access_token}
        sheets.InsertRow(data, spreadsheet_key, 1)


def put_event_to_calendar(calendar_id, data, date):
    if settings.NOTIFICATION_DISABLED:
        return

    from accounts.models import Configuration

    try:
        client_email = Configuration.objects.get(system='web.spreadsheet.configuration', key='client_email').value
        key = Configuration.objects.get(system='web.spreadsheet.configuration', key='key').value
    except Configuration.DoesNotExist:
        return
    else:
        from oauth2client.client import SignedJwtAssertionCredentials

        json_key = json.loads(key)
        scope = ['https://www.googleapis.com/auth/calendar']

        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

        from httplib2 import Http
        http_auth = credentials.authorize(Http())

        from apiclient.discovery import build
        service = build('calendar', 'v3', http=http_auth)

        event = {
          'summary': data['title'],
          'location': data['address'],
          'description': data['description'],
          'start': {
            'dateTime': date.isoformat(),
          },
          'end': {
            'dateTime': date.isoformat(),
          }
        }
        resp = service.events().insert(calendarId=calendar_id, body=event).execute()
        return resp


def delete_calendar_events(calendar_id, event_id):

    from accounts.models import Configuration

    try:
        client_email = Configuration.objects.get(system='web.spreadsheet.configuration', key='client_email').value
        key = Configuration.objects.get(system='web.spreadsheet.configuration', key='key').value
    except Configuration.DoesNotExist:
        return
    else:
        from oauth2client.client import SignedJwtAssertionCredentials

        json_key = json.loads(key)
        scope = ['https://www.googleapis.com/auth/calendar']

        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

        from httplib2 import Http
        http_auth = credentials.authorize(Http())

        from apiclient.discovery import build
        service = build('calendar', 'v3', http=http_auth)
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()


def timeout_handler():
    raise Exception("Reach execution timeout, aborted.")


def safe_eval(code, variables):
    aeval = Interpreter()

    for key, value in variables.iteritems():
        aeval.symtable[key] = value

    # TODO: signal do not work on main thread
    # signal.signal(signal.SIGALRM, timeout_handler)
    # signal.alarm(5)
    return aeval(code)


def multi_level_dict_to_one_level_dict(data, key_level='', result={}):
    for key, value in data.iteritems():
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            pass
        # Check type(value) == 'dict' 
        if isinstance(value, dict):
            key_level_next = '%s%s.' % (key_level, key)
            multi_level_dict_to_one_level_dict(value, key_level=key_level_next, result=result)
        else:
            # print '%s%s' % (key_level, key)
            result['%s%s' % (key_level, key)] = value
    return result


def get_system_user():
    from common.models import Domain, get_current_domain_id

    user_model = get_user_model()

    try:
        system_user = user_model.objects.get(username='system')
    except user_model.DoesNotExist:
        try:
            system_user = user_model.objects.create_user('system', 'system@system.com', uuid.uuid4().get_hex())
        except (ValidationError, IntegrityError) as e:
            system_user = user_model.default_manager.get(username='system')
            current_domain = Domain.objects.get(id=get_current_domain_id())
            system_user.domains.add(current_domain)

    return system_user


def get_public_authority(domain_id=None):
    from common.models import get_current_domain_id
    from accounts.models import Authority

    if not domain_id:
        domain_id = get_current_domain_id()

    try:
        authority = Authority.objects.get(code='public_%s' % domain_id, domain_id=domain_id)
    except Authority.DoesNotExist:
        authority = Authority.objects.create(code='public_%s' % domain_id, name='public_%s' % domain_id,
                                             description='public', domain_id=domain_id)

    return authority


def get_public_area(domain_id=None):
    from common.models import get_current_domain_id
    from reports.models import AdministrationArea

    if not domain_id:
        domain_id = get_current_domain_id()

    authority = get_public_authority(domain_id)

    code = 'public_%s' % domain_id
    area, created = AdministrationArea.objects.get_or_create(code=code, authority=authority, defaults={
        'code': code,
        'authority': authority,
        'name': code,
        'location': 'POINT (100.552206 13.808277)',
        'domain_id': domain_id

    })

    return area


def randstr():
    return str(uuid1())[0: 10].replace('-', '')


def email_title_render_template(email_title, authority):
    if authority:
        try:
            template_email_title = Configuration.objects.get(system='web.email_templete.%s' % authority.name, key='title').value
        except Configuration.DoesNotExist:
            template_email_title = '{{ title }}'
    else:
        template_email_title = '{{ title }}'

    tt = Template(template_email_title)
    cc = Context({
        'title': email_title
    })
    return tt.render(cc)


def email_body_render_template(email_body, user, authority):
    if authority:
        try:
            template_email_body = Configuration.objects.get(system='web.email_templete.%s' % authority.name, key='body').value
        except Configuration.DoesNotExist:
            template_email_body = '{{ body|linebreaksbr|safe }}'
    else:
        template_email_body = 'เรียน {{ name }}, <br/>{{ body }}'

    tt = Template(template_email_body)
    cc = Context({
        'name': user.name,
        'body': email_body
    })

    return tt.render(cc)


def send_email_with_template(email_title, email_body, to_email):
    message = EmailMultiAlternatives(email_title,
                                     email_body,
                                     settings.EMAIL_ADDRESS_NO_REPLY,
                                     to_email)
    message.attach_alternative(email_body, "text/html")
    message.send()


def clean_phone_numbers(value):

    value = value or ''
    result = []

    for telephone in value.split(','):
        telephones = re.sub('[^0-9]', ' ', telephone)
        telephones = re.sub(' {2,}', ',', telephones).replace(' ', '').split(',')
        telephone = max(telephones, key=len)
        if telephone:
            result.append(telephone)

    return result


def clean_emails(value):

    value = value or ''
    result = []

    for email in value.split(','):
        email = re.findall(r'[\w\.-]+@[\w\.-]+', email)
        if len(email):
            email = email[0]
            result.append(email)

    return result


import math

UTM_NORTHERN_BASE = 32600
UTM_SOUTHERN_BASE = 32700

DEFAULT_MAP_SRID = 3857


def get_utm_zone(point):
	"""
		Guess the UTM zone ID for the supplied point
	"""
	# hardcode the target reference system:
	# this is WGS84 by spec
	wgspoint = point.transform('WGS84', clone=True)
	# remember, geographers are sideways
	lon = wgspoint.x
	return int(1 + (lon + 180.0) / 6.0)

def is_utm_northern(point):
	"""
		Determine if the supplied point is in the northern or southern part
		for the UTM coordinate system.
	"""
	wgspoint = point.transform('WGS84', clone=True)
	lat = wgspoint.y
	return lat >= 0.0

def get_utm_srid(point):
	"""
		Given the input point, guess the UTM zone and hemissphere and
		return the SRID for the UTM appropriate UTM zone.

		Note that this does not do any range checking, so supplying bogus
		points yields undefined results.
	"""
	utm_zone = get_utm_zone(point)
	is_northern = is_utm_northern(point)
	if is_northern:
		return UTM_NORTHERN_BASE + utm_zone
	else:
		return UTM_SOUTHERN_BASE + utm_zone

def buffer_from_meters(geom, buffer_meters):
	"""
		Create a buffer around the supplied geometry
		with the specified distance.

		This is a wrapper around GEOMSGeometry.buffer()
		but with the buffer distance specified in meters.

		GEOM should be in the coordinate system the map will be drawn in,
		this is usually "web mercator", i.e. EPSG:3857
	"""
	# The buffer calculation needs to happen in the source
	# coordinate system, otherwise stretching occurs
	# (e.g. circles become more and more egg-like further away from the equator)
	#
	# At the same time we want distances in meters to be
	# as close to correct as possible given the local environment.
	#
	# The approach taken here is
	# (1) use the centroid of the input geometry to determine a single reference
	#     point
	# (2) transform this reference point into the appropriate UTM coordinate system
	#     This is done using the correct UTM zone for the reference put.
	#     to keep differences to a minimum.
	# (3) shift the UTM version of the reference point to the north and east
	#     by buffer_meters / sqrt(2).
	# (4) transform the shifted point back from UTM to the input coordinate system
	#     and calculate the distance between the shifted point and the original point
	#     in the input coordinate system.
	# (5) Use this newly obtain distance value to create
	#     a buffered geometry from the original.
	ref_point = geom.centroid.clone()
	if not ref_point.srid:
		# default to WGS84
		ref_point.srid = 4326

	utm_srid = get_utm_srid(ref_point)
	utm_point = ref_point.transform(utm_srid, clone=True)

	shift_distance = buffer_meters / math.sqrt(2.0)
	shifted_point = utm_point.clone()
	shifted_point.set_x(shifted_point.get_x() + shift_distance)
	shifted_point.set_y(shifted_point.get_y() + shift_distance)

	shifted_ref = shifted_point.transform(ref_point.srid, clone=True)

	distance = shifted_ref.distance(ref_point)
	return distance