from django.db import models

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф.И.О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", related_name='clients')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", related_name='messages')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['-created_at']

    def __str__(self):
        return self.subject[:50]


class Mailing(models.Model):
    class Status(models.TextChoices):
        CREATED = 'created', 'Создана'
        RUNNING = 'running', 'Запущена'
        COMPLETED = 'completed', 'Завершена'

    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name="Статус"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
        related_name='mailings'
    )
    recipients = models.ManyToManyField(
        Client,
        verbose_name="Получатели",
        related_name='mailings'
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", related_name='mailings')
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-created_at']

    def __str__(self):
        return f"Рассылка #{self.id} - {self.message.subject[:30]}"

    def update_status(self):
        """Обновляет статус рассылки на основе текущего времени"""
        now = timezone.now()
        old_status = self.status

        if now < self.start_time:
            new_status = self.Status.CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.Status.RUNNING
        else:
            new_status = self.Status.COMPLETED

        if old_status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

        return self.status

    def clean(self):
        """Валидация данных"""
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Дата начала должна быть раньше даты окончания")

            if self.start_time < timezone.now():
                raise ValidationError("Дата начала не может быть в прошлом")


class MailingAttempt(models.Model):
    """Модель попытки отправки рассылки"""

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успешно'
        FAILED = 'failed', 'Не успешно'

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Статус"
    )
    server_response = models.TextField(verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name="Рассылка",
        related_name='attempts'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name="Получатель",
        related_name='attempts'
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Попытка {self.attempt_time} - {self.status}"
