# coding=utf-8

from optparse import make_option
import random
import string
from django.core.management import BaseCommand

from accounts.models import Authority
from notifications.models import LineMessageGroup

class Command(BaseCommand):
    help = u'''
    generate default line invite number for all authorities.
    '''
    option_list = BaseCommand.option_list + (
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Whether to force mode, default is dry_run mode'
        ),
    )
    def handle(self, *args, **options):
        dry_run = not options['force']

        # select all authority.id without touching orm
        authorities = Authority.objects.all().values_list('id', flat=True)

        # generate 7 digit line invite number for each authority
        generated = set()
        for authority in authorities:
            #random 7 digit number string
            line_invite_number = ''.join(random.choice(string.digits) for _ in range(7))
            # check if generated number is unique
            while line_invite_number in generated:
                line_invite_number = ''.join(random.choice(string.digits) for _ in range(7))
            generated.add((authority, line_invite_number))
        
        # create LineMessageGroup for each authority
        for authority, line_invite_number in generated:
            if not dry_run:
                LineMessageGroup.objects.create(
                    authority_id=authority,
                    invite_number=line_invite_number
                )
            else:
                print('authority_id: %s, invite_number: %s' % (authority, line_invite_number))
