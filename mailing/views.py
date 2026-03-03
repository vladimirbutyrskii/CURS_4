from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm, MailingForm
import logging

logger = logging.getLogger(__name__)


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр рассылки с автоматическим обновлением статуса"""
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Автоматически обновляем статус при просмотре
        obj.update_status()
        return obj


@login_required
def home(request):
    """Главная страница со статистикой"""

    # Общее количество рассылок пользователя
    total_mailings = Mailing.objects.filter(owner=request.user).count()

    # Количество активных рассылок
    now = timezone.now()
    active_mailings = Mailing.objects.filter(
        owner=request.user,
        start_time__lte=now,
        end_time__gte=now,
        status=Mailing.Status.RUNNING
    ).count()

    # Количество уникальных получателей
    total_clients = Client.objects.filter(owner=request.user).count()

    # Статистика по попыткам
    attempts_stats = MailingAttempt.objects.filter(
        mailing__owner=request.user
    ).values('status').annotate(count=Count('id'))

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'total_clients': total_clients,
        'attempts_stats': attempts_stats,
    }
    return render(request, 'mailing/home.html', context)


# CRUD для клиентов
@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, 'mailing/client_list.html', {'clients': clients})


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            messages.success(request, 'Клиент успешно создан')
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'mailing/client_form.html', {'form': form, 'title': 'Создание клиента'})


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент успешно обновлен')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'mailing/client_form.html', {'form': form, 'title': 'Редактирование клиента'})


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Клиент успешно удален')
        return redirect('client_list')
    return render(request, 'mailing/client_confirm_delete.html', {'client': client})


# CRUD для сообщений
@login_required
def message_list(request):
    messages_list = Message.objects.filter(owner=request.user)
    return render(request, 'mailing/message_list.html', {'messages': messages_list})


@login_required
def message_create(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.owner = request.user
            message.save()
            messages.success(request, 'Сообщение успешно создано')
            return redirect('message_list')
    else:
        form = MessageForm()
    return render(request, 'mailing/message_form.html', {'form': form, 'title': 'Создание сообщения'})


@login_required
def message_update(request, pk):
    message = get_object_or_404(Message, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сообщение успешно обновлено')
            return redirect('message_list')
    else:
        form = MessageForm(instance=message)
    return render(request, 'mailing/message_form.html', {'form': form, 'title': 'Редактирование сообщения'})


@login_required
def message_delete(request, pk):
    message = get_object_or_404(Message, pk=pk, owner=request.user)
    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Сообщение успешно удалено')
        return redirect('message_list')
    return render(request, 'mailing/message_confirm_delete.html', {'message': message})


# CRUD для рассылок
@login_required
def mailing_list(request):
    mailings = Mailing.objects.filter(owner=request.user)
    return render(request, 'mailing/mailing_list.html', {'mailings': mailings})


@login_required
def mailing_create(request):
    if request.method == 'POST':
        form = MailingForm(request.user, request.POST)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.owner = request.user
            mailing.save()
            form.save_m2m()  # Сохраняем связи многие-ко-многим
            messages.success(request, 'Рассылка успешно создана')
            return redirect('mailing_list')
    else:
        form = MailingForm(request.user)
    return render(request, 'mailing/mailing_form.html', {'form': form, 'title': 'Создание рассылки'})


@login_required
def mailing_update(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MailingForm(request.user, request.POST, instance=mailing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рассылка успешно обновлена')
            return redirect('mailing_list')
    else:
        form = MailingForm(request.user, instance=mailing)
    return render(request, 'mailing/mailing_form.html', {'form': form, 'title': 'Редактирование рассылки'})


@login_required
def mailing_delete(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
    if request.method == 'POST':
        mailing.delete()
        messages.success(request, 'Рассылка успешно удалена')
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_confirm_delete.html', {'mailing': mailing})


@login_required
def send_mailing(request, pk):
    """Ручной запуск рассылки"""
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
    mailing.update_status()  # Обновляем статус перед проверкой

    # Проверяем, можно ли отправить рассылку
    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        messages.error(request, 'Рассылку можно отправить только в период между датой начала и окончания')
        return redirect('mailing_detail', pk=pk)

    recipients = mailing.recipients.all()
    success_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            # Отправка письма
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            # Запись об успешной попытке
            MailingAttempt.objects.create(
                status=MailingAttempt.Status.SUCCESS,
                server_response='Письмо успешно отправлено',
                mailing=mailing,
                client=recipient
            )
            success_count += 1

        except Exception as e:
            logger.error(f"Ошибка отправки письма: {str(e)}")

            # Запись о неудачной попытке
            MailingAttempt.objects.create(
                status=MailingAttempt.Status.FAILED,
                server_response=str(e)[:200],  # Ограничиваем длину
                mailing=mailing,
                client=recipient
            )
            failed_count += 1

    messages.success(
        request,
        f'Рассылка завершена. Успешно: {success_count}, Ошибок: {failed_count}'
    )
    return redirect('mailing_detail', pk=pk)


# Кешированный список клиентов
@login_required
@cache_page(60 * 15)  # Кешируем на 15 минут
def cached_client_list(request):
    clients = Client.objects.filter(owner=request.user).select_related('owner')
    return render(request, 'mailing/client_list.html', {'clients': clients, 'cached': True})


# Статистика с кешированием
@login_required
def mailing_statistics(request):
    stats_cache_key = f'user_stats_{request.user.id}'
    stats = cache.get(stats_cache_key)

    if not stats:
        # Если нет в кеше, вычисляем
        mailings = Mailing.objects.filter(owner=request.user)

        total_mailings = mailings.count()

        now = timezone.now()
        active_mailings = mailings.filter(
            start_time__lte=now,
            end_time__gte=now,
            status=Mailing.Status.RUNNING
        ).count()

        total_clients = Client.objects.filter(owner=request.user).count()

        attempts = MailingAttempt.objects.filter(mailing__owner=request.user)
        successful_attempts = attempts.filter(status=MailingAttempt.Status.SUCCESS).count()
        failed_attempts = attempts.filter(status=MailingAttempt.Status.FAILED).count()

        stats = {
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'total_clients': total_clients,
            'successful_attempts': successful_attempts,
            'failed_attempts': failed_attempts,
        }

        # Сохраняем в кеш на 10 минут
        cache.set(stats_cache_key, stats, 60 * 10)

    return render(request, 'mailing/statistics.html', {'stats': stats})

