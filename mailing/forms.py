from django import forms
from django.utils import timezone
from .models import Client, Message, Mailing


class ClientForm(forms.ModelForm):
    """Форма для создания/редактирования клиента"""

    class Meta:
        model = Client
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    """Форма для создания/редактирования сообщения"""

    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class MailingForm(forms.ModelForm):
    """Форма для создания/редактирования рассылки"""
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user.is_manager:
            # Менеджеры видят все сообщения и клиентов
            self.fields['message'].queryset = Message.objects.all()
            self.fields['recipients'].queryset = Client.objects.all()
        else:
            # Пользователи - только свои
            self.fields['message'].queryset = Message.objects.filter(owner=user)
            self.fields['recipients'].queryset = Client.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Дата начала должна быть раньше даты окончания")

            if start_time < timezone.now():
                raise forms.ValidationError("Дата начала не может быть в прошлом")

        return cleaned_data
