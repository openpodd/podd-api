from django.core.management import BaseCommand, CommandError

from accounts.models import User, UserDevice
from firebase.functions import send_fcm_notification


class Command(BaseCommand):
    args = 'username message_title message_body'
    help = 'send message to username via fcm'

    def handle(self, *args, **options):
        if len(args) < 3:
            raise CommandError('Please provider username, message title and body')
        username = args[0]
        title = args[1]
        body = args[2]

        current_user = User.objects.get(username=username)
        device = UserDevice.objects.get(user=current_user)
        if device.fcm_reg_id:
            send_fcm_notification(device.fcm_reg_id, title, body)
        else:
            print("fcm_reg_id not found\n")
