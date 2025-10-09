from django.contrib import admin
from .models import Category, SubCategory, PremiumProfileLink, InvalidUsernameEmail

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
