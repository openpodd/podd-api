# -*- encoding: utf-8 -*-

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from analysis.models import Word
from common.functions import get_data_from_csv


class Command(BaseCommand):
    args = 'word_for_analysis.csv'
    help = 'Import words from csv: word_for_analysis.csv'

    def handle(self, *args, **options):

        if not args:
            raise CommandError('Please input csv path')

        file_path = args[0]
        data = get_data_from_csv(file_path)

        for row in data:
            if not row[u'th_word'] and not row[u'en_word']:
                continue

            th_word = row['th_word']
            en_word = row['en_word']

            word, created = Word.objects.get_or_create(
                th_word = th_word,
                en_word =en_word,
            )

