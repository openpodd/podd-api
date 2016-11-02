
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q

from accounts.models import User
from logs.models import LogItem


def list_for_object(obj):
    content_type = ContentType.objects.get_for_model(obj)

    q = Q(object_type1=content_type, object_id1=obj.pk) \
        | Q(object_type2=content_type, object_id2=obj.pk)

    logs = LogItem.objects.filter(q).select_related('created_by').distinct()

    return logs


def list_for_content_type(content_type):
    content_type = ContentType.objects.get_for_model(content_type)
    q = Q(object_type1=content_type) | Q(object_type2=content_type)

    logs = LogItem.objects.filter(q).select_related('created_by').distinct()

    return logs


def list_for_user(user):
    logs = LogItem.objects.filter(created_by=user).select_related('created_by')

    return logs


def object_detail(content_type_id, pk):
    ct = ContentType.objects.get(pk=content_type_id)
    obj = ct.get_object_for_this_type(pk=pk)
    return obj
