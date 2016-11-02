import re

from django.core.exceptions import ObjectDoesNotExist

from accounts.models import User
from mentions.models import Mention
from mentions.serializers import MentionSerializer
from reports.pub_tasks import publish_mention
from reports.models import ReportComment

def create_mentions(comment_id, message):
    comment = ReportComment.objects.get(id=comment_id)
    split_mentionees = re.split(r"@\[(?P<username>[\w\-]+)\]", message)
    mentionees = User.objects.filter(username__in=split_mentionees)

    for mentionee in mentionees:

        print 'comment', comment

        mention = Mention.objects.create(
            comment = comment,
            mentioner = comment.created_by,
            mentionee = mentionee
        )
        if comment.created_by == mentionee:
            mention.is_notified = True
            mention.save()

        mentionee_id = mention.mentionee.id
        serializer = MentionSerializer(mention)
        serializer.data['mentioneeId'] = mentionee_id
        publish_mention(serializer.data)
   