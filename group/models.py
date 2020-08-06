from django.db import models
from django.utils import timezone

from background_task.models import Task, CompletedTask


class Blacklist(models.Model):
    link = models.TextField(
        verbose_name='Ссылка'
    )

    def __str__(self):
        return 'Нежелательная ссылка ({})'.format(self.link)

    class Meta:
        verbose_name = 'Нежелательная ссылка'
        verbose_name_plural = 'Нежелательные ссылки'


class GlobalSettings(models.Model):
    setting = models.TextField(
        verbose_name='Настройка',
    )
    value = models.TextField(
        verbose_name='Значение',
    )

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'


class Gratitudes(models.Model):
    word = models.CharField(
        max_length=32,
        verbose_name='Слово благодарности',
    )

    def __str__(self):
        return 'Слово благодарности'

    class Meta:
        verbose_name = 'Слово благодарности'
        verbose_name_plural = 'Слова благодарности'


class Groups(models.Model):
    id = models.IntegerField(
        primary_key=True,
        unique=True,
    )
    title = models.CharField(
        max_length=32,
    )
    messages_in_last_interval = models.IntegerField(
        default=0,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Members(models.Model):
    id = models.IntegerField(
        primary_key=True,
        unique=True,
    )
    username = models.CharField(
        max_length=32,
        blank=True,
        null=True,
    )
    private_chat_id = models.IntegerField(
        unique=True,
        blank=True,
        null=True,
    )
    is_admin = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.username


class GroupsLog(models.Model):
    group_id = models.IntegerField(
        verbose_name='ID Группы',
    )
    group_title = models.CharField(
        max_length=32,
        verbose_name='Название Группы',
    )
    added_by = models.ForeignKey(
        Members,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='added_by',
        verbose_name='Добавивший',
    )
    is_processed = models.BooleanField(
        default=False,
        verbose_name='Запрос обработан?',
    )
    processed_by = models.ForeignKey(
        Members,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_by',
        verbose_name='Оработавший',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Добавлен',
    )

    def __str__(self):
        return 'Запись об активации бота'

    class Meta:
        verbose_name = 'Запись об активации бота'
        verbose_name_plural = 'Записи об активации бота'


class Info(models.Model):
    user = models.ForeignKey(
        Members,
        on_delete=models.PROTECT,
        verbose_name='Пользователь',
    )
    chat = models.ForeignKey(
        Groups,
        on_delete=models.PROTECT,
        verbose_name='Название чата',
    )
    rating = models.IntegerField(
        default=0,
        verbose_name='Рейтинг'
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата вступления в группу'
    )
    mute_rating = models.IntegerField(
        default=0,
        verbose_name='Кол-во нарушений',
    )

    def __str__(self):
        return "Объект базы пользователей"

    class Meta:
        unique_together = ('user', 'chat')
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ScheduledMessages(models.Model):
    id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(
        Groups,
        on_delete=models.PROTECT,
        verbose_name='Группа',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    interval = models.DurationField(
        verbose_name='Интервал',
    )
    task_id = models.CharField(
        verbose_name='Уникальный номер задачи',
        max_length=32,
        blank=True,
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
        verbose_name = 'Нецензурное выражение'
        verbose_name_plural = 'Нецензурные выражения'


class Whitelist(models.Model):
    word = models.CharField(max_length=32)

    def __str__(self):
        return 'Допустимое слово'

    class Meta:
        verbose_name = 'Допустимое слово'
        verbose_name_plural = 'Допустимые слова'
