from django.apps import AppConfig
from django.conf import settings
from firebase_admin import credentials
import firebase_admin


class FireAppConfig(AppConfig):

    name = 'firebase'
    verbose_name = 'firebase'

    @staticmethod
    def initialize_podd_chat():
        if settings.FIREBASE_SERVICE_ACCOUNT_CERT:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CERT)
            FireAppConfig.app = firebase_admin.initialize_app(cred, {
                'databaseURL': settings.FIREBASE_PODD_CHAT_URL
            })

    @staticmethod
    def initialize_podd_firebase_app():
        if settings.FIREBASE_SERVICE_ACCOUNT_CERT_PODD:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CERT_PODD)
            FireAppConfig.app = firebase_admin.initialize_app(cred, {
                'databaseURL': settings.FIREBASE_PODD_URL
            }, 'podd')

    def ready(self):
        self.initialize_podd_chat()
        self.initialize_podd_firebase_app()