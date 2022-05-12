from django.db import models

from accounts.models import Authority
from common.models import DomainMixin


class LetterFieldConfiguration(DomainMixin):
    code = models.CharField(max_length=30)
    authority = models.ForeignKey(Authority)
    header_address1 = models.CharField(max_length=255)
    header_address2 = models.CharField(max_length=255)
    sign_name = models.CharField(max_length=300)
    sign_position1 = models.CharField(max_length=300)
    sign_position2 = models.CharField(max_length=300)
    footer_contact_line1 = models.CharField(max_length=300)
    footer_contact_line2 = models.CharField(max_length=300)
    footer_contact_line3 = models.CharField(max_length=300)