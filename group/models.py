from django.db import models
from django.utils import timezone


class Blacklist(models.Model):
    link = models.TextField(
        verbose_name='Ссылка'
    )

    def __str__(self):
        return 'Нежелательная ссылка ({})'.format(self.link)

    class Meta:
        verbose_name = 'Черный список ссылок'
        verbose_name_plural = 'Черный список ссылок'


class Gratitudes(models.Model):
    word = models.CharField(max_length=32)

    def __str__(self):
        return 'Слово благодарности'

    class Meta:
        verbose_name = 'Список слов благодарности'
        verbose_name_plural = 'Список слов благодарности'


class Groups(models.Model):
    id = models.IntegerField(
        verbose_name='ID Группы',
        primary_key=True,
        unique=True,
    )
    title = models.CharField(
        max_length=32,
        verbose_name='Название Группы',
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Members(models.Model):
    id = models.IntegerField(
        verbose_name='ID Пользователя',
        primary_key=True,
        unique=True,
    )
    username = models.CharField(
        max_length=32,
        verbose_name='Ник Пользователя',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Info(models.Model):
    user = models.ForeignKey(Members, on_delete=models.PROTECT)
    chat = models.ForeignKey(Groups, on_delete=models.PROTECT)
    rating = models.IntegerField(default=0)
    date_joined = models.DateTimeField(default=timezone.now)
    mute_rating = models.IntegerField(
        default=0,
        verbose_name='Кол-во нарушений',
    )

    class Meta:
        unique_together = ('user', 'chat')
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинг'


class ScheduledMessages(models.Model):
    id = models.AutoField(primary_key=True)
    chat = models.IntegerField(
        verbose_name='Группа',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    interval = models.DurationField(
        verbose_name='Интервал',
    )

    def __str__(self):
        return 'Запланированное сообщение №{}'.format(self.id)

    class Meta:
        db_table = 'group_scheduled_messages'
        verbose_name = 'Запланированное сообщение'
        verbose_name_plural = 'Запланированные сообщения'


class Swearing(models.Model):
    word = models.CharField(max_length=32)

    def __str__(self):
        return 'Нецензурное слово'

    class Meta:
        verbose_name = 'Список нецензурных слов'
        verbose_name_plural = 'Список нецензурных слов'