from django.db import models

# Create your models here.
from common.models import DomainMixin


class Monitoring(DomainMixin):
    uploadedfile = models.FileField(upload_to = 'media/monitoring/%Y/%m/%d')
    created_at = models.DateTimeField(auto_now_add=True)

