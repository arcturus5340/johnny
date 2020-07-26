from django.db import models
from django.utils import timezone


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

