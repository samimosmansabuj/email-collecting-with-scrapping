from django.db import models
from core.models import Category, SubCategory

class EmailTemplateContent(models.Model):
    category = models.ManyToManyField(Category, related_name="email_templates", blank=True)
    sub_category = models.ManyToManyField(SubCategory, related_name="email_templates", blank=True)
    body = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    for_proficiency = models.CharField(max_length=255, blank=True, null=True)
    response_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    positive_rating = models.PositiveIntegerField(default=0, blank=True, null=True)
    
    def __str__(self):
        return f"Email Template for {self.sub_category} | {self.subject}"

class EmailAttachment(models.Model):
    template = models.ForeignKey(EmailTemplateContent, on_delete=models.SET_NULL, related_name="email_attachments", blank=True, null=True)
    file = models.FileField("email-template-file/", blank=True, null=True)
    
    def __str__(self):
        return f"Attachment File for {self.template.subject}"


class EmailConfig(models.Model):
    server = models.CharField(blank=True, max_length=50, null=True)
    email = models.EmailField(max_length=255)
    host_user = models.CharField(max_length=255)
    host_password = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.CharField(max_length=10)
    tls = models.BooleanField(default=True)
    ssl = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    today_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    daily_limit = models.PositiveIntegerField(blank=True, null=True)
    today_date = models.DateField(blank=True, null=True)
    today_complete = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def increase_today_count(self):
        self.today_count+=1
        if self.today_count == self.daily_limit:
            self.today_complete = True
    
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
    
    
    
    def __str__(self):
        return f"{self.email} | {self.host} | LIMIT {self.daily_limit} | Active: {self.is_active}"



