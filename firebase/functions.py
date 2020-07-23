import logging
import re
import time

from firebase_admin.messaging import UnregisteredError
from podd.celery import app

from firebase_admin import db
from firebase_admin import messaging


@app.task
def send_fcm_notification(fcm_reg_id, title, body):
    messaging.send(messaging.Message(
        token=fcm_reg_id,
        notification=messaging.Notification(
            title=title,
            body=body
        )
    ))


@app.task
def send_fcm_message(message, message_type, report_id, notification_id, fcm_reg_id):
    data = {
        'id': str(notification_id) or '',
        'message': message,
        'type': message_type,
        'reportId': str(report_id) or ''
    }
    try:
        message = messaging.Message(
            data=data,
            token=fcm_reg_id,
        )
    except UnregisteredError:
        logging.info('UnregisteredError: %s' % fcm_reg_id)
        from notifications.tasks import deregister_fcm_from_user_device
        deregister_fcm_from_user_device.delay(fcm_reg_id)

    messaging.send(message)


def create_room(domain_id, room_id, user_id, user_name, room_name, welcome_msg, meta=None):
    '''
    :param domain_id:
    :param room_id:
    :param user_id:
    :param user_name:
    :param room_name:
    :param welcome_msg:
    :param meta:
    :return: success status
    '''
    if meta is None:
        meta = {}
    db.reference('/%s/rooms/%s' % (domain_id, room_id)).set({
        'description': room_name,
        'assigned': False,
        'done': False,
        'ts': int(time.time() * 1000),
        'meta': meta
    })
    db.reference('/%s/messages/%s' % (domain_id, room_id)).push({
        'userId': user_id,
        'username': user_name,
        'message': welcome_msg,
        'ts': int(time.time() * 1000)
    })
    return True


def create_token(domain_id, room_id, user_id, user_name, authority_id, authority_name):
    '''
    :param domain_id:
    :param room_id:
    :param user_id:
    :param user_name:
    :param authority_id:
    :param authority_name:
    :return:
    '''
    user_key = '%s:%s:%s' % (room_id, user_id, user_name)
    user_key = re.sub(
        r"[.\[\]()]",
        "_",
        user_key
    )
    token_map_ref = db.reference('/%s/tokenMap/%s' % (domain_id, user_key))
    token_map = token_map_ref.get()
    if token_map:
        return token_map
    token_ref = db.reference('/tokens').push({
        'roomId': room_id,
        'domainId': domain_id,
        'userId': user_id,
        'username': user_name,
        'authorityId': authority_id,
        'authorityName': authority_name,
        'ts': int(time.time() * 1000)
    })
    token_map_ref.set(token_ref.key)

    db.reference('/%s/rooms/%s/members' % (domain_id, room_id)).child(token_ref.key).set({
        'joined': False,
        'answered': False,
        'authorityId': authority_id,
        'authorityName': authority_name,
        'username': user_name
    })
    return token_ref.key


def post_message(domain_id, room_id, user_id, user_name, message, image_url=None, meta=None):
    '''
    :param domain_id:
    :param room_id:
    :param user_id:
    :param user_name:
    :param message:
    :param image_url:
    :param meta:
    :return:
    '''
    if meta is None:
        meta = {}
    msg_obj = {
        'message': message,
        'ts': int(time.time() * 1000),
        'username': user_name,
        'userId': user_id,
        'meta': meta
    }

    if image_url:
        msg_obj['imageUrl'] = image_url

    db.reference('/%s/messages/%s' % (domain_id, room_id)).push(msg_obj)
    return True