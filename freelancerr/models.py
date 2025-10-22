from django.db import models
from core.models import Category, SubCategory
from core.model_select_choice import FOLLOW_UP_STAGE,LEAD_STAGE
import re

class FreelancerCompleteProfileDetails(models.Model):
    DETAILS_TYPE = [("project", "project"), ("profile", "profile")]
    username = models.CharField(max_length=50)
    details_type = models.CharField(max_length=10, choices=DETAILS_TYPE, default="project")
    url = models.CharField(max_length=255, unique=True)
    
    total_reviews = models.PositiveIntegerField(default=0)
    total_scrapping = models.PositiveIntegerField(default=0)
    collecting_email = models.PositiveIntegerField(default=0)
    total_update = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.details_type} | {self.url})"

class FreelancerReviewListWithEmail(models.Model):
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, blank=True, null=True)
    review_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    most_important = models.BooleanField(default=False)
    send_main = models.BooleanField(default=False)
    follow_up = models.BooleanField(default=False)
    follow_up_stage = models.CharField(max_length=50, choices=FOLLOW_UP_STAGE, blank=True, null=True)
    lead_stage = models.CharField(max_length=50, choices=LEAD_STAGE, blank=True, null=True)
    
    def extract_amount(self, price_tag: str):
        clean = price_tag.replace(",", "")
        match = re.findall(r"\d+", clean)
        return int("".join(match)) if match else None
    
    def get_price_proficiency(self, price_str):
        symbol_map = {
            "$": "Very Low",
            "$$": "Low",
            "$$$": "Medium",
            "$$$$": "Very High",
        }
        if price_str in symbol_map:
            return symbol_map[price_str].lower()
        
        amount = self.extract_amount(price_str)
        if amount is None:
            return "medium"
        
        if "INR" in price_str or "₹" in price_str:
            thresholds = [8500, 17000, 42000, 67000, 85000, 130000]
        else:  # AUD, USD, CAD, EUR, GBP
            thresholds = [100, 200, 500, 800, 1000, 1500]
        
        levels = ["Very Low", "Low", "Medium", "High", "Very High", "Important", "Most Important"]
        
        for i, th in enumerate(thresholds):
            if amount < th:
                return levels[i].lower()
        return levels[-1].lower()
    
    def save(self, *args, **kwargs):
        self.proficiency = self.get_price_proficiency(self.price_tag) if self.price_tag != "N/A" else "medium"
        
        if self.country:
            try:
                print(f"self.country.split(',') [{self.country}]: ", self.country.split(",")[1])
                country = self.country.split(",")[1]
            except:
                country = self.country
            self.country = country.strip()
        
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} | {self.email} | {self.proficiency}"
    
