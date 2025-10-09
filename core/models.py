from django.db import models
from django.utils.text import slugify

class PremiumProfileLink(models.Model):
    SOURCE = (
        ("fiverr", "fiverr"),
        ("freelancer", "freelancer"),
    )
    source = models.CharField(max_length=20, choices=SOURCE, blank=True, null=True)
    url = models.URLField(max_length=255)
    is_scrapping = models.BooleanField(default=False)
    
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

def generate_unique_slug(model_object, field_value, old_slug=None):
    slug = slugify(field_value)
    if slug != old_slug:
        unique_slug = slug
        num = 1
        while model_object.objects.filter(slug=unique_slug).exists():
            if unique_slug == old_slug:
                return old_slug
            unique_slug = f'{slug}-{num}'
            num+=1
        return unique_slug
    else:
        return old_slug

