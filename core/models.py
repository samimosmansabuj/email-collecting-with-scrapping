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


class EmailTemplateContent(models.Model):
    category = models.ManyToManyField(Category, related_name="email_templates", blank=True, null=True)
    sub_category = models.ManyToManyField(SubCategory, related_name="email_templates", blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    for_proficiency = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Email Template for {self.sub_category} | {self.subject}"

class EmailAttachment(models.Model):
    template = models.ForeignKey(EmailTemplateContent, on_delete=models.SET_NULL, related_name="email_attachments", blank=True, null=True)
    file = models.FileField("email-template-file/", blank=True, null=True)
    
    def __str__(self):
        return f"Attachment File for {self.template.subject}"
    

