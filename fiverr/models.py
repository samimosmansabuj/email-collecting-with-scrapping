from django.db import models
import re

class CompleteGigDetails(models.Model):
    DETAILS_TYPE = [("gig", "gig"), ("profile", "profile")]
    username = models.CharField(max_length=50)
    details_type = models.CharField(max_length=10, choices=DETAILS_TYPE, default="gig")
    url = models.CharField(max_length=255, unique=True)
    
    total_reviews = models.PositiveIntegerField(default=0)
    total_scrapping = models.PositiveIntegerField(default=0)
    collecting_email = models.PositiveIntegerField(default=0)
    total_update = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.details_type} | {self.url})"

class ReviewListWithEmail(models.Model):
    PROFICIENCY = [
        ("very low", "very low"),
        ("low", "low"),
        ("medium", "medium"),
        ("high", "high"),
        ("very high", "very high"),
        ("important", "important"),
        ("most important", "most important"),
    ]
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=255)
    repeated = models.BooleanField(default=False)
    country = models.CharField(max_length=50)
    price_tag = models.CharField(max_length=50, default="N/A")
    proficiency = models.CharField(max_length=55, choices=PROFICIENCY, blank=True, null=True)
    time_text = models.CharField(max_length=55, default="N/A")
    count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=55, blank=True, null=True)
    sub_category = models.CharField(max_length=55, blank=True, null=True)
    review_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def get_price_proficiency(self, price_str):
        price_str = price_str.replace(",", "").replace("US$", "").replace("$", "").strip()
        nums = re.findall(r"\d+(?:\.\d+)?", price_str)
        
        if not nums:
            return "Medium"
        
        price = float(nums[0])
        if price <= 50:
            return "very low"
        elif price <= 200:
            return "low"
        elif price <= 600:
            return "medium"
        elif price <= 1000:
            return "high"
        elif price <= 2000:
            return "very high"
        elif price <= 4000:
            return "important"
        else:
            return "most important"
    
    def save(self, *args, **kwargs):
        self.proficiency = self.get_price_proficiency(self.price_tag) if self.price_tag != "N/A" else "medium"
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} | {self.email} | {self.proficiency}"
    

    

