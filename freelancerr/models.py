from django.db import models
from core.models import Category, SubCategory
from core.model_select_choice import FOLLOW_UP_STAGE,LEAD_STAGE
from send_mail.models import EmailConfig
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
    
    # update only When mail send-----------------
    send_mail = models.BooleanField(default=False)
    last_mail_server = models.ForeignKey(EmailConfig, on_delete=models.SET_NULL, related_name="freelancer_send_mails", blank=True, null=True)
    last_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Webhook or Mail Status Callback-----------------
    last_event = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    last_event_at = models.DateTimeField(blank=True, null=True)
    last_provider_ts = models.BigIntegerField(blank=True, null=True)
    follow_up = models.BooleanField(default=False)
    follow_up_stage = models.CharField(max_length=50, choices=FOLLOW_UP_STAGE, blank=True, null=True)
    lead_stage = models.CharField(max_length=50, choices=LEAD_STAGE, blank=True, null=True)
    
    deferred_count = models.PositiveIntegerField(default=0)
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    send_count = models.PositiveIntegerField(default=0)
    
    
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
    
    
    def reset_lead(self):
        self.send_mail = False
        self.follow_up = False
    
    def update_follow_up_and_lead_stage(self, event):
        if event in {"delivered"}:
            self.send_count = (self.send_count or 0) + 1
            self.follow_up_stage = FOLLOW_UP_STAGE.STAGE_01
            self.lead_stage = self.lead_stage or LEAD_STAGE.NOT_RESPONSE
            self.follow_up = True
        elif event in {"opened", "unique_opened"}:
            self.open_count = (self.open_count or 0) + 1
            self.follow_up_stage = FOLLOW_UP_STAGE.STAGE_03
            self.lead_stage = LEAD_STAGE.FOLLOW_UP
            self.follow_up = True
        elif event in {"click"}:
            self.click_count = (self.click_count or 0) + 1
            self.follow_up_stage = FOLLOW_UP_STAGE.STAGE_04
            self.lead_stage = LEAD_STAGE.RESPONSE
            self.follow_up = True
        elif event in {"unsubscribed", "blocked"}:
            self.follow_up_stage = FOLLOW_UP_STAGE.STAGE_06
            self.lead_stage = LEAD_STAGE.NOT_QUALIFIED
            self.reset_lead()
        elif event in {"hard_bounce", "soft_bounce", "spam", "error", "deferred", "invalid_email", "proxy_open", "unique_proxy_open"}:
            self.deferred_count = (self.deferred_count or 0) + 1
            # if self.deferred_count >= 3:
            self.follow_up_stage = FOLLOW_UP_STAGE.STAGE_06
            self.lead_stage = LEAD_STAGE.LOST
            self.follow_up = False
    
    def save(self, *args, **kwargs):
        self.proficiency = self.get_price_proficiency(self.price_tag) if self.price_tag != "N/A" else "medium"
        if self.country:
            try:
                print(f"self.country.split(',') [{self.country}]: ", self.country.split(",")[1])
                country = self.country.split(",")[1]
            except:
                country = self.country
            self.country = country.strip()
        self.update_follow_up_and_lead_stage(self.last_event)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} | {self.email} | {self.proficiency}"
    
