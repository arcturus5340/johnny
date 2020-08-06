from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils.html import format_html
from background_task import background

import uuid

from group import models
from group import forms
from group.telegram_bot_api import API

from background_task.models import Task, CompletedTask


@admin.register(models.Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ('link', )
    search_fields = ('link', )


@admin.register(models.Gratitudes)
class GratitudesAdmin(admin.ModelAdmin):
    list_display = ('word',)


@admin.register(models.GroupsLog)
class GroupsLogAdmin(admin.ModelAdmin):
    readonly_fields = list_display = (
        'group_title',
        'group_id',
        'added_by_info',
        'is_processed',
        'processed_by_info',
        'created_at',
    )
    list_filter = ('group_title',)

    def added_by_info(self, obj):
        return '{} (ID: {})'.format(obj.added_by.username, obj.added_by.id)
    added_by_info.short_description = 'Добавивший'

    def processed_by_info(self, obj):
        return '{} (ID: {})'.format(obj.processed_by.username, obj.processed_by.id)
    processed_by_info.short_description = 'Обработавший'

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.GroupsBlacklist)
class GroupsBlacklistAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
    )


@admin.register(models.Info)
class InfoAdmin(admin.ModelAdmin):
    readonly_fields = list_display = ('user__id', 'user', 'chat', 'rating', 'mute_rating', 'date_joined')
    list_filter = ('chat',)

    def user__id(self, obj):
        return obj.user.id

    def has_add_permission(self, request, obj=None):
        return False


@background
def send_message(chat_id, text):
    group = models.Groups.objects.get(id=chat_id)
    if group.messages_in_last_interval > 9:
        API.sendMessage(chat_id, text)
        group.messages_in_last_interval = 0
        group.save()


@admin.register(models.ScheduledMessages)
class ScheduledMessagesAdmin(admin.ModelAdmin):
    form = forms.ScheduledMessagesForm
    list_display = ('chat', 'text', 'interval')

    def save_model(self, request, obj, form, change):
        obj.task_id = obj.task_id or uuid.uuid4().hex
        send_message(obj.chat.id, obj.text, repeat=obj.interval.total_seconds(), verbose_name=obj.task_id)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        Task.objects.filter(verbose_name=obj.task_id).delete()
        CompletedTask.objects.filter(verbose_name=obj.task_id).delete()
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            Task.objects.filter(verbose_name=obj.task_id).delete()
            CompletedTask.objects.filter(verbose_name=obj.task_id).delete()
        return super().delete_queryset(request, queryset)

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(models.Swearing)
class SwearingAdmin(admin.ModelAdmin):
    list_display = search_fields =('word',)

@admin.register(models.Whitelist)
class WhitelistAdmin(admin.ModelAdmin):
    list_display = search_fields =('word',)


admin.site.index_title = 'Админиcтрирование ботов'
admin.site.site_title = 'Sharewood'
admin.site.site_header = 'Sharewood Administration'
admin.site.unregister(Group)
admin.site.unregister(User)
