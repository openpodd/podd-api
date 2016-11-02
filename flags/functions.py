# -*- encoding: utf-8 -*-

import re

from common.constants import PRIORITY_CHOICES, PRIORITY_IGNORE

from accounts.models import Configuration
from mentions.functions import create_mentions
from reports.models import ReportComment
from reports.pub_tasks import publish_comment
from reports.serializers import ReportCommentSerializer


def create_flag_comment(report, priority, flag_owner):
    try:
        template_for_flag =  Configuration.objects.get(system='web.template.report', key='comment_flag').value
    except Configuration.DoesNotExist:
        template_for_flag = u'@[%(username)s] ได้ทำการตั้งค่าความสำคัญเป็น %(flag)s'

    try:
        flag = filter(lambda s: s[0] == priority, PRIORITY_CHOICES)[0]
    except IndexError:
        flag = (PRIORITY_IGNORE, 'Ignore')

    message = template_for_flag % {'username': flag_owner.username, 'flag': flag[1]}

    comment = ReportComment.objects.create(
        report = report,
        message = message,
        created_by = flag_owner,
    )

    # serializer = ReportCommentSerializer(comment)
    # publish_comment(serializer.data)
    # create_mentions(serializer.object.id, serializer.object.message)

    return comment

    