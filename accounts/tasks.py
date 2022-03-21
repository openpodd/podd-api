# -*- encoding: utf-8 -*-
import json
import os
import codecs
import hashlib

from django.conf import settings as django_settings
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.db import connection
from django.template import Template, Context
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Configuration, Authority
from common.functions import publish_sms_message, email_title_render_template, email_body_render_template, send_email_with_template
from podd.celery import app


@app.task
def send_alert_forgot_password_sms(user, uid=None, token=None, code=None):
    telephones = [(user.project_mobile_number or user.telephone)]
    if telephones:
        try:
            forgot_password_sms = Configuration.objects.get(system='web.sms_templete.forgot_password', key='message').value
        except Configuration.DoesNotExist:
            forgot_password_sms = u'รหัสผ่านชั่วคราวของคุณคือ: {{ code }} ' \
                                    + u'โดยรหัสผ่านนี้จะหมดอายุเมื่อ {{ expired }}'

        tt = Template(forgot_password_sms)
        cc = Context({
            'code': code.code,
            'expired': code.expired,
            'uid': uid or urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token or token_generator.make_token(user),
            'site_url': settings.SITE_URL
        })

        forgot_password_sms_rendered = tt.render(cc)
        publish_sms_message(message=forgot_password_sms_rendered, telephones=telephones)


@app.task
def send_alert_forgot_password_email(user, uid=None, token=None, code=None):
    email = user.email
    if email:

        try:
            forgot_password_email_title = Configuration.objects.get(system='web.email_templete.forgot_password', key='title').value
        except Configuration.DoesNotExist:
            forgot_password_email_title = u'รหัสผ่านชั่วคราว'

        try:
            forgot_password_email_body = Configuration.objects.get(system='web.email_templete.forgot_password', key='body').value
        except Configuration.DoesNotExist:
            forgot_password_email_body = u'รหัสผ่านชั่วคราวของคุณคือ: {{ code }} ' \
                                    + u'โดยรหัสผ่านนี้จะหมดอายุเมื่อ {{ expired }}'

        email_title_template_rendered = forgot_password_email_title

        tt = Template(forgot_password_email_body)
        cc = Context({
            'code': code.code,
            'expired': code.expired,
            'uid': uid or urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token or token_generator.make_token(user),
            'site_url': settings.SITE_URL
        })

        email_body_template_rendered = tt.render(cc)

        authorities = Authority.objects.filter(users=user)
        authority = authorities[0] if authorities.count() else None

        email_tile = email_title_render_template(email_title_template_rendered, authority)
        email_body = email_body_render_template(email_body_template_rendered, user, authority)

        send_email_with_template(email_tile, email_body, [email])


@app.task
def send_alert_register_complete(user):
    email = user.email
    if email:

        try:
            register_complete_email_title = Configuration.objects.get(system='web.email_templete.register_complete', key='title').value
        except Configuration.DoesNotExist:
            register_complete_email_title = u'การลงทะเบียนสำเร็จ'

        try:
            register_complete_email_body = Configuration.objects.get(system='web.email_templete.register_complete', key='body').value
        except Configuration.DoesNotExist:
            register_complete_email_body = u'ชื่อบัญชีผู้ใช้: {{ username }} '  \
                                    + u'รหัสผ่านของคุณคือ {{ password }}'

        email_title_template_rendered = register_complete_email_title

        tt = Template(register_complete_email_body)
        cc = Context({
            'username': user.username,
            'password': user.display_password,
            'site_url': settings.SITE_URL
        })

        email_body_template_rendered = tt.render(cc)

        authorities = Authority.objects.filter(users=user)
        authority = authorities[0] if authorities.count() else None

        email_tile = email_title_render_template(email_title_template_rendered, authority)
        email_body = email_body_render_template(email_body_template_rendered, user, authority)

        send_email_with_template(email_tile, email_body, [email])


@app.task
def send_alert_change_password_complete(user):
    email = user.email
    if email:

        try:
            password_complete_email_title = Configuration.objects.get(system='web.email_templete.password_complete', key='title').value
        except Configuration.DoesNotExist:
            password_complete_email_title = u'เปลี่ยนรหัสผ่านสำเร็จ'

        try:
            password_complete_email_body = Configuration.objects.get(system='web.email_templete.password_complete', key='body').value
        except Configuration.DoesNotExist:
            password_complete_email_body = u'ชื่อบัญชีผู้ใช้: {{ username }} '  \
                                    + u'รหัสผ่านของคุณคือ {{ password }}'

        email_title_template_rendered = password_complete_email_title

        tt = Template(password_complete_email_body)
        cc = Context({
            'username': user.username,
            'password': user.display_password,
            'site_url': settings.SITE_URL
        })

        email_body_template_rendered = tt.render(cc)

        authorities = Authority.objects.filter(users=user)
        authority = authorities[0] if authorities.count() else None

        email_tile = email_title_render_template(email_title_template_rendered, authority)
        email_body = email_body_render_template(email_body_template_rendered, user, authority)

        send_email_with_template(email_tile, email_body, [email])


@app.task
def generate_area_files():
    """
    create static area file and hash checksum in /static/area
    :return:
    """

    def dict_fetch_all(cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    cursor = connection.cursor()
    cursor.execute("""
        select l.id   as id,
               l.name as name,
               a.id   as di_id,
               a.name as di_name,
               p.name as pv_name,
               p.id   as pv_id,
               ra.id  as area_id
        from accounts_authority p,
             accounts_authority a,
             accounts_authority_inherits pa,
             accounts_authority l,
             accounts_authority_inherits al,
             reports_administrationarea ra
        where p.name like 'จังหวัด%'
          and a.id = pa.from_authority_id
          and p.id = pa.to_authority_id
          and l.id = al.from_authority_id
          and a.id = al.to_authority_id
          and l.id = ra.authority_id
          and ra.id = l.default_area_id  
        order by a.id  
    """)
    data = dict_fetch_all(cursor)
    json_object = json.dumps(data, indent=2, ensure_ascii=False)
    target_file = os.path.join(django_settings.STATIC_ROOT, 'area', 'area.json')
    hash_file = os.path.join(django_settings.STATIC_ROOT, 'area', 'area.md5')
    with codecs.open(target_file, mode="wb", encoding="UTF8") as outfile:
        outfile.write(json_object)
    with open(hash_file, mode="w") as out_hash_file:
        out_hash_file.write(hashlib.md5(json_object.encode("UTF8")).hexdigest())
