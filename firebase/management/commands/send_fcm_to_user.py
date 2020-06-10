from django.core.management import BaseCommand, CommandError

from accounts.models import User, UserDevice
from common.functions import publish_fcm_message


class Command(BaseCommand):
    args = 'username message'
    help = 'send message to username via fcm'

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError('Please provider username, message')
        username = args[0]
        message = args[1]

        current_user = User.objects.get(username=username)
        device = UserDevice.objects.get(user=current_user)
        if device.fcm_reg_id:
            publish_fcm_message([device.fcm_reg_id], message, "news")
        else:
            print("fcm_reg_id not found\n")
