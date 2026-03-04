from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .models import User
from .forms import UserRegistrationForm
import logging

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Деактивируем до подтверждения email
            user.save()

            # Отправка письма для подтверждения email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                reverse_lazy('verify_email', kwargs={'uidb64': uid, 'token': token})
            )

            try:
                send_mail(
                    subject='Подтверждение email',
                    message=f'Перейдите по ссылке для подтверждения: {verification_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
                messages.success(request, 'Пожалуйста, подтвердите ваш email. Проверьте почту.')
                return redirect('login')
            except Exception as e:
                logger.error(f"Ошибка отправки письма: {e}")
                messages.error(request, 'Ошибка при отправке письма. Попробуйте позже.')
                user.delete()  # Удаляем пользователя при ошибке
                return redirect('register')
    else:
        form = UserRegistrationForm()
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
        return redirect('login')
    else:
        messages.error(request, 'Ссылка для подтверждения недействительна')
        return redirect('register')

