from django.db import models
from .utils import generate_unique_slug

class PremiumProfileLink(models.Model):
    SOURCE = (
        ("fiverr", "fiverr"),
        ("freelancer", "freelancer"),
    )
    source = models.CharField(max_length=20, choices=SOURCE, blank=True, null=True)
    url = models.URLField(max_length=255)
    is_scrapping = models.BooleanField(default=False)
    most_important = models.BooleanField(default=False)
    
    def __str__(self):
        return self.url

class Category(models.Model):
    name = models.CharField(max_length=55)
    slug = models.SlugField(max_length=55, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        old_slug = Category.objects.get(pk=self.pk) if self.pk else None
        self.slug = generate_unique_slug(Category, self.name, old_slug.slug if old_slug else None)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=55)
    slug = models.SlugField(max_length=55, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        old_slug = SubCategory.objects.get(pk=self.pk) if self.pk else None
        self.slug = generate_unique_slug(SubCategory, self.name, old_slug.slug if old_slug else None)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class InvalidUsernameEmail(models.Model):
    username = models.CharField(max_length=50)
    status_code = models.CharField(max_length=10, blank=True, null=True)
    def __str__(self):
        return self.username

class WebHookServer(models.TextChoices):
    BREVO = "brevo"
    MAILEROO = "maileroo"

class WebhookEventLogs(models.Model):
    server = models.CharField(max_length=25, choices=WebHookServer, default=WebHookServer.BREVO)
    server_account = models.CharField(max_length=50, blank=True, null=True)
    webhook_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        email = self.webhook_json.get("email")
        event = self.webhook_json.get("event")
        return f"{self.pk} | {self.server} | {self.server_account} | {email} | {event}"

class EmailOpenLog(models.Model):
    mail_server_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    ip = models.CharField(max_length=50, blank=True, null=True)
    open_count = models.PositiveIntegerField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.pk} | {self.mail_server_name} | {self.email} | {self.open_count}"


# class Role(models.Model):
#     title = models.CharField(max_length=55)
    

