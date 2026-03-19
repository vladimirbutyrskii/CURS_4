from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['email', 'full_name']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['subject']


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'status', 'owner', 'start_time', 'end_time', 'is_active']
    list_filter = ['status', 'owner', 'is_active', 'start_time']
    search_fields = ['message__subject']
    filter_horizontal = ['recipients']


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ['attempt_time', 'mailing', 'client', 'status']
    list_filter = ['status', 'attempt_time']
    search_fields = ['mailing__message__subject', 'client__email']
