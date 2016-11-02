
from accounts.models import Configuration
from common.pub_tasks import publish


def publish_user_profile(data):
    publish('user:avatar:new', data)
