# -*- encoding: utf-8 -*-

import unittest
from common.functions import clean_phone_numbers, clean_emails


class TestAPICleanPhoneNumbers(unittest.TestCase):

    def test_phone_numbers_with_single_user(self):

        phone_numbers = u'นายกยุนอา 089-112-4567'
        results = clean_phone_numbers(phone_numbers)
        self.assertEqual(results, ['0891124567'])

    def test_phone_numbers_with_multiple_user(self):

        phone_numbers = u'นายกยุนอา 089-112-4567, รองนายกแทยอน 086-0019345'
        results = clean_phone_numbers(phone_numbers)
        self.assertEqual(results, ['0891124567', '0860019345'])

    def test_phone_numbers_with_emails(self):

        phone_numbers = u'นายกยุนอา 089-112-4567, รองนายกแทยอน taeyeon@mail.com'
        results = clean_phone_numbers(phone_numbers)
        self.assertEqual(results, ['0891124567'])


class TestAPICleanEmails(unittest.TestCase):

    def test_emails_with_single_user(self):

        emails = u'นายกยุนอา yoona@mail.com'
        results = clean_emails(emails)
        self.assertEqual(results, ['yoona@mail.com'])

    def test_emails_with_multiple_user(self):

        emails = u'นายกยุนอา yoona@mail.com, รองนายกแทยอน taeyeon@mail.com'
        results = clean_emails(emails)
        self.assertEqual(results, ['yoona@mail.com', 'taeyeon@mail.com'])

    def test_emails_with_phone_numbers(self):

        emails = u'นายกยุนอา 089-112-4567, รองนายกแทยอน taeyeon@mail.com'
        results = clean_emails(emails)
        self.assertEqual(results, ['taeyeon@mail.com'])