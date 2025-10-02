from django.contrib import admin
from .models import CompleteGigDetails, ReviewListWithEmail, InvalidUsernameEmail


@admin.register(CompleteGigDetails)
class CompleteGigDetailsAdmin(admin.ModelAdmin):
    list_display = (
        "username", "details_type", "url",
        "total_reviews", "total_scrapping", "collecting_email", "total_update",
        "created_at", "updated_at",
    )
    list_filter = (
        "details_type",
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
    )
    search_fields = ("username", "url")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"
    list_per_page = 50
    # readonly_fields = ("created_at", "updated_at")  # uncomment if you want to lock these in admin

@admin.register(ReviewListWithEmail)
class ReviewListWithEmailAdmin(admin.ModelAdmin):
    list_display = (
        "username", "email", "proficiency", "price_tag",
        "country", "count", "category", "sub_category",
        "time_text", "repeated", "created_at", "updated_at",
    )
    list_filter = (
        "proficiency", "repeated", "country", "category", "sub_category",
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "username", "email", "country", "price_tag", "time_text", "review_description",
        "category__name", "sub_category__name",
    )
    ordering = ("-updated_at", "-created_at")
    date_hierarchy = "updated_at"
    list_per_page = 50


@admin.register(InvalidUsernameEmail)
class InvalidUsernameEmailAdmin(admin.ModelAdmin):
    list_display = (
        "username", "status_code"
    )
    search_fields = (
        "username", "status_code"
    )
    list_per_page = 50
