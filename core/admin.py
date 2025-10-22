from django.contrib import admin
from .models import Category, SubCategory, PremiumProfileLink, InvalidUsernameEmail, EmailTemplateContent, EmailAttachment

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(PremiumProfileLink)

@admin.register(InvalidUsernameEmail)
class InvalidUsernameEmailAdmin(admin.ModelAdmin):
    list_display = (
        "username", "status_code"
    )
    search_fields = (
        "username", "status_code"
    )
    list_per_page = 50

admin.site.register(EmailTemplateContent)
admin.site.register(EmailAttachment)
