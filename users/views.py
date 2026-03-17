import sys

import traceback

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .models import User
from .forms import UserRegistrationForm
import logging

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация нового пользователя"""
    # print("\n" + "=" * 50, file=sys.stdout)
    # print("=== НАЧАЛО РЕГИСТРАЦИИ ===", file=sys.stdout)
    # print(f"Метод запроса: {request.method}", file=sys.stdout)
    # print("=" * 50, file=sys.stdout)

    if request.method == 'POST':
        # print("Обработка POST запроса", file=sys.stdout)
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            # print("Форма валидна", file=sys.stdout)

            # Создаем пользователя
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # print(f"Пользователь создан:", file=sys.stdout)
            # print(f"  - ID: {user.pk}", file=sys.stdout)
            # print(f"  - Username: {user.username}", file=sys.stdout)
            # print(f"  - Email: {user.email}", file=sys.stdout)
            # print(f"  - is_active: {user.is_active}", file=sys.stdout)

            # Создаем токен и ссылку
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                reverse('users:verify_email', kwargs={'uidb64': uid, 'token': token})
            )

            # print(f"\nТокен подтверждения: {token}", file=sys.stdout)
            # print(f"UID (кодированный): {uid}", file=sys.stdout)
            # print(f"UID (раскодированный): {user.pk}", file=sys.stdout)
            # print(f"Полная ссылка для подтверждения: {verification_url}", file=sys.stdout)

            # Информация о настройках email
            # print(f"\nНастройки email:", file=sys.stdout)
            # print(f"  - EMAIL_BACKEND: {settings.EMAIL_BACKEND}", file=sys.stdout)
            # print(f"  - DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}", file=sys.stdout)

            try:
                # print("\nПытаюсь отправить письмо...", file=sys.stdout)

                # Отправляем письмо
                send_mail(
                    subject='Подтверждение email',
                    message=f'Перейдите по ссылке для подтверждения: {verification_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                # print("✓ Письмо успешно отправлено!", file=sys.stdout)
                # print("✓ Проверьте консоль выше - там должно быть полное письмо", file=sys.stdout)

                messages.success(request, 'Пожалуйста, подтвердите ваш email. Проверьте почту.')
                return redirect('users:login')

            except Exception as e:
                # print(f"\n✗ ОШИБКА при отправке письма!", file=sys.stdout)
                # print(f"  - Тип ошибки: {type(e).__name__}", file=sys.stdout)
                # print(f"  - Текст ошибки: {str(e)}", file=sys.stdout)
                # print("\nПолный traceback:", file=sys.stdout)
                # traceback.print_exc(file=sys.stdout)

                user.delete()
                messages.error(request, 'Ошибка при отправке письма. Попробуйте позже.')
                return redirect('users:register')
        # else:
        #     print("Форма невалидна", file=sys.stdout)
        #     print(f"Ошибки формы: {form.errors}", file=sys.stdout)
    else:
        # print("GET запрос - показываем форму", file=sys.stdout)
        form = UserRegistrationForm()

    # print("=" * 50 + "\n", file=sys.stdout)
    return render(request, 'users/register.html', {'form': form})


def verify_email(request, uidb64, token):
    """Подтверждение email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Email успешно подтвержден. Теперь вы можете войти.')
        return redirect('users:login')
    else:
        messages.error(request, 'Ссылка для подтверждения недействительна')
        return redirect('users:register')

