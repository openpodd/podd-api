
import datetime

from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.utils.html import format_html
from accounts.models import User
from common.constants import NEWS_TYPE_NEWS

from .models import News
from notifications.models import Notification
from .pub_tasks import publish_news


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    fields = ('type', 'message', 'area', 'authority', 'created_by', 'published_at')
    readonly_fields = ('created_by', 'published_at')
    list_display = ('__unicode__', 'is_published')
    actions = ['make_published']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def is_published(self, obj):
        if obj.published_at:
            icon_url = static('admin/img/icon-yes.gif')
        else:
            icon_url = static('admin/img/icon-no.gif')

        return format_html('<img src="{0}" alt="{1}" />', icon_url, obj.published_at)

    def make_published(self, request, queryset):
        rows_updated = 0
        for news in queryset:
            if not news.published_at:
                rows_updated += 1
                news.published_at = datetime.datetime.now()
                news.save()

                if news.authority:
                    receive_user_list = news.authority.get_users_all()
                else:
                    receive_user_list = User.objects.filter(domains=news.domain, is_active=True)

                for receive_user in receive_user_list:
                    Notification.objects.create(
                        receive_user=receive_user,
                        to=receive_user.username,
                        created_by=news.created_by,
                        type=NEWS_TYPE_NEWS,
                        message=news.message
                    )

        if rows_updated:
            self.message_user(request, "%s news were successfully marked as published." % rows_updated)

    make_published.short_description = "Mark selected news as published"