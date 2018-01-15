from django.apps import AppConfig
from django.conf import settings
from firebase_admin import credentials
import firebase_admin


class FireAppConfig(AppConfig):

    name = 'firebase'
    verbose_name = 'firebase'

    def ready(self):
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CERT)
        FireAppConfig.app = firebase_admin.initialize_app(cred)