from django.contrib import admin
from .models import Category, SubCategory, PremiumProfileLink

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(PremiumProfileLink)
