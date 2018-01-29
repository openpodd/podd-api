from django.apps import AppConfig
from django.conf import settings
from firebase_admin import credentials
import firebase_admin


class FireAppConfig(AppConfig):

    name = 'firebase'
    verbose_name = 'firebase'

    def ready(self):
        if settings.FIREBASE_SERVICE_ACCOUNT_CERT:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CERT)
            FireAppConfig.app = firebase_admin.initialize_app(cred, {
                'databaseURL': settings.FIREBASE_PODD_CHAT_URL
            })