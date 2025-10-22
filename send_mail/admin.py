from django.contrib import admin
from .models import EmailAttachment, EmailTemplateContent, EmailConfig

admin.site.register(EmailTemplateContent)
admin.site.register(EmailAttachment)
admin.site.register(EmailConfig)
