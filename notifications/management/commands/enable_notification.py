from django.core.management import BaseCommand, CommandError

from notifications.models import NotificationTemplate, NotificationAuthority


class Command(BaseCommand):
    help = 'create notification_authority'
    def handle(self, *args, **options):
        if not args:
            raise CommandError("please specific template id")

        template_id = int(args[0])

        template = NotificationTemplate.objects.get(pk=template_id)
        root_authority = template.authority
        pass_authority_ids = set([])

        def enable(authority):
            if authority.id in pass_authority_ids:
                return
            pass_authority_ids.add(authority.id)

            try:
                NotificationAuthority.objects.get(template=template, authority=authority)
            except NotificationAuthority.DoesNotExist:
                NotificationAuthority.objects.create(template=template, authority=authority, domain=template.domain)

            for child in authority.authority_inherits.all():
                enable(child)

        enable(root_authority)






