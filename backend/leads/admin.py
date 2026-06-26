from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'company', 'ai_category', 'ai_priority', 'submission_time', 'email_sent')
    list_filter = ('ai_category', 'ai_priority', 'email_sent', 'email_opened', 'link_clicked')
    search_fields = ('full_name', 'email', 'company')
    readonly_fields = ('tracking_id', 'submission_time', 'email_sent_at', 'email_opened_at', 'open_count', 'link_clicked_at', 'click_count')
