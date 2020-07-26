from django.db import models
from django.utils import timezone


class Blacklist(models.Model):
    link = models.TextField(
        verbose_name='Ссылка'
    )

    class Meta:
        verbose_name = 'Черный список ссылок'
        verbose_name_plural = 'Черный список ссылок'


class Members(models.Model):
    user = models.IntegerField(
        verbose_name='ID Пользователя'
    )
    chat = models.IntegerField(
        verbose_name='ID Группы'
    )
    date_joined = models.DateTimeField(default=timezone.now)
    rating = models.IntegerField(
        default=0,
        verbose_name='Репутация'
    )
    mute_rating = models.IntegerField(
        default=0,
        verbose_name='Кол-во нарушений'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ScheduledMessages(models.Model):
    chat = models.IntegerField(
        verbose_name='Группа'
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    interval = models.DurationField(
        verbose_name='Интервал'
    )

    class Meta:
        db_table = 'group_scheduled_messages'
        verbose_name = 'Запланированное сообщение'
        verbose_name_plural = 'Запланированные сообщения'


class Swearing(models.Model):
    word = models.CharField(max_length=32)
