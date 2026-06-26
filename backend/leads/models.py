import uuid
from django.db import models

class Lead(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    company = models.CharField(max_length=255, blank=True, null=True)
    requirement = models.TextField()
    submission_time = models.DateTimeField(auto_now_add=True)
    
    tracking_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    email_opened = models.BooleanField(default=False)
    email_opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    
    link_clicked = models.BooleanField(default=False)
    link_clicked_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    
    ai_category = models.CharField(max_length=100, blank=True, null=True)
    ai_priority = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
