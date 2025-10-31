from django.contrib import admin
from .models import EmailAttachment, EmailTemplateContent, EmailConfig

# admin.site.register(EmailTemplateContent)
# admin.site.register(EmailAttachment)
# admin.site.register(EmailConfig)

# admin.py
from django.contrib import admin
from .models import EmailTemplateContent, EmailAttachment, EmailConfig


class EmailAttachmentInline(admin.TabularInline):
    model = EmailAttachment
    extra = 1


@admin.register(EmailTemplateContent)
class EmailTemplateContentAdmin(admin.ModelAdmin):
    # inlines = [EmailAttachmentInline]

    list_display = (
        "type",
        "is_active",
        "subject",
        "for_proficiency",
        "response_count",
        "positive_rating",
    )
    list_filter = (
        "is_active",
        "type",
        "category",
        "sub_category",
    )
    search_fields = ("subject", "body")
    readonly_fields = ("response_count", "positive_rating")
    filter_horizontal = ("category", "sub_category")

    fieldsets = (
        ("Basic Info", {
            "fields": ("type", "subject", "body", "is_active", "for_proficiency"),
        }),
        ("Categorization", {
            "fields": ("category", "sub_category"),
        }),
        ("Stats (read-only)", {
            "fields": ("response_count", "positive_rating"),
        }),
    )


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "file")
    search_fields = ("template__subject",)
    autocomplete_fields = ("template",)


@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "name",
        "host",
        "port",
        "is_active",
        "is_default",
        "tls",
        "ssl",
        "type",
        "daily_limit",
        "today_count",
        "today_complete",
        "today_date",
    )
    list_filter = ("is_active", "is_default", "tls", "ssl", "host", "type")
    search_fields = ("email", "server", "host_user", "host", "type")
    readonly_fields = ()
    actions = ("mark_active", "mark_inactive", "reset_today_count")

    fieldsets = (
        ("Connection", {
            "fields": ("server", "api_key", "name", "email", "host_user", "host_password", "host", "port", "type"),
        }),
        ("Security", {
            "fields": ("tls", "ssl"),
        }),
        ("Status & Limits", {
            "fields": ("is_default", "is_active", "daily_limit", "today_count", "today_date", "today_complete"),
        }),
    )

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} configuration(s) marked active.")
    mark_active.short_description = "Mark selected as active"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} configuration(s) marked inactive.")
    mark_inactive.short_description = "Mark selected as inactive"

    def reset_today_count(self, request, queryset):
        updated = queryset.update(today_count=0, today_complete=False)
        self.message_user(request, f"{updated} configuration(s) had today's count reset.")
    reset_today_count.short_description = "Reset today_count & today_complete"

