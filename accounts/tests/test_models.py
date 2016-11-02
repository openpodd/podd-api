import datetime
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from accounts.models import Authority


class TestSafety(TestCase):

    def setUp(self):
        pass

    def test_invite(self):

        authority = Authority.objects.create(
            code='chiangmai',
            name='Chiang mai',
        )

        mpd = settings.MINUTES_PER_DAY
        expire_days = settings.AUTHORITY_INVITE_EXPIRE_DAYS
        today = timezone.now()

        old_invite = authority.get_invite()
        origin_invite = authority.renew_invite()

        self.assertNotEqual(old_invite, origin_invite)

        with freeze_time(today + datetime.timedelta(minutes=mpd * (expire_days-1))):
            self.assertEqual(origin_invite, authority.get_invite())

        with freeze_time(today + datetime.timedelta(minutes=mpd * (expire_days+0))):
            self.assertEqual(origin_invite, authority.get_invite())

        with freeze_time(today + datetime.timedelta(minutes=mpd * (expire_days+1))):
            self.assertNotEqual(origin_invite, authority.get_invite())


    def test_deep_subscribes(self):

        a1 = Authority.objects.create(code='a1', name='a1')

        a11 = Authority.objects.create(code='a11', name='a11')
        a11.inherits.add(a1)

        a12 = Authority.objects.create(code='a12', name='a12')
        a12.inherits.add(a1)

        a2 = Authority.objects.create(code='a2', name='a2')

        # Check add deep subscribes
        a2.deep_subscribes.add(a1)

        self.assertEqual([a1.id, a11.id, a12.id], list(a2.get_subscribes_all()))

        # Add children auto add to subscribers
        a111 = Authority.objects.create(code='a111', name='a111')
        a111.inherits.add(a11)

        self.assertEqual([a1.id, a11.id, a12.id, a111.id], list(a2.get_subscribes_all()))

        # Remove children auto remove from subscribers
        a111.inherits.remove(a11)
        self.assertEqual([a1.id, a11.id, a12.id], list(a2.get_subscribes_all()))

        # Check remove deep subscribes
        a2.deep_subscribes.remove(a1)
        self.assertEqual([], list(a2.get_subscribes_all()))

        # Check circular
        a11.inherits.add(a1)
        a11.inherits.add(a111)

        a1.inherits.add(a111)
        a111.inherits.add(a1)


        # Check clear deep subscribes
        a2.deep_subscribes.add(a1)

        a111.inherits.clear()
        a11.inherits.clear()
        self.assertEqual([a1.id, a12.id], list(a2.get_subscribes_all()))

        # Check subscribe inherit not sucscribe self
        a1.inherits.clear()
        a11.inherits.clear()
        a12.inherits.clear()
        a111.inherits.clear()

        a11.inherits.add(a1)
        a12.inherits.add(a1)
        a111.inherits.add(a11)

        a11.deep_subscribes.add(a1)
        self.assertEqual([a1.id, a12.id], list(a11.get_subscribes_all()))

        a112 = Authority.objects.create(code='a112', name='a112')
        a112.inherits.add(a11)
        self.assertEqual([a1.id, a12.id], list(a11.get_subscribes_all()))



