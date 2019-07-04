from django.core.management.base import BaseCommand, CommandError

from accounts.models import User, Authority


class Command(BaseCommand):
    args = 'user_id to_authority_id'
    help = 'change current authority of given user'

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError('Please provide user_id and to_authority_id')

        user_id = args[0]
        to_authority_id = args[1]

        current_user = User.objects.get(pk=user_id)
        auths = current_user.authority_users.all()
        if len(auths) > 1:
            raise CommandError('Number of authorities is more than 1')

        current_authority = auths[0]
        target_authority = Authority.objects.get(pk=to_authority_id)

        current_authority.users.remove(current_user)
        target_authority.users.add(current_user)