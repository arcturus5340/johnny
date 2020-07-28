from django.contrib import admin
from django.contrib.auth.models import User, Group

from group import models
from group import forms

@admin.register(models.Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ('link', )


@admin.register(models.Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')


@admin.register(models.Members)
class MembersAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'rating', 'mute_rating')


@admin.register(models.Swearing)
class SwearingAdmin(admin.ModelAdmin):
    list_display = ('word', )


@admin.register(models.ScheduledMessages)
class ScheduledMessagesAdmin(admin.ModelAdmin):
    form = forms.ScheduledMessagesForm
    list_display = ('chat', 'text', 'interval')


admin.site.index_title = 'Админиcтрирование ботов'
admin.site.site_title = 'Sharewood'
admin.site.site_header = 'Sharewood Administration'
admin.site.unregister(Group)
admin.site.unregister(User)
