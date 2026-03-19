from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from mailing.models import Mailing, MailingAttempt
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запуск рассылки по ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        try:
            mailing = Mailing.objects.get(id=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Рассылка с ID {mailing_id} не найдена'))
            return

        # Обновляем статус
        mailing.update_status()

        # Проверяем время
        now = timezone.now()
        if not (mailing.start_time <= now <= mailing.end_time):
            self.stdout.write(
                self.style.ERROR('Рассылку можно отправить только в период между датой начала и окончания')
            )
            return

        recipients = mailing.recipients.all()
        success_count = 0
        failed_count = 0

        self.stdout.write(f'Начинаем отправку рассылки #{mailing_id} для {recipients.count()} получателей')

        for recipient in recipients:
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                MailingAttempt.objects.create(
                    status=MailingAttempt.Status.SUCCESS,
                    server_response='Письмо успешно отправлено',
                    mailing=mailing,
                    client=recipient
                )
                success_count += 1
                self.stdout.write(f'✓ {recipient.email} - успешно')

            except Exception as e:
                logger.error(f"Ошибка отправки письма {recipient.email}: {str(e)}")

                MailingAttempt.objects.create(
                    status=MailingAttempt.Status.FAILED,
                    server_response=str(e)[:200],
                    mailing=mailing,
                    client=recipient
                )
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'✗ {recipient.email} - ошибка: {str(e)[:50]}...'))

        self.stdout.write(
            self.style.SUCCESS(f'Рассылка завершена. Успешно: {success_count}, Ошибок: {failed_count}')
        )
