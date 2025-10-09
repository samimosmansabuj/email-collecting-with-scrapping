from django.urls import path
from .views import freelancer_data, get_subcategories, ScrapFreelancerDataView, freelancer_result, verify_freelancer_url

urlpatterns = [
    path('freelancer/data-list/', freelancer_data, name="freelancerr_data"),
    path('freelancer/scrap-new-data/', ScrapFreelancerDataView.as_view(), name="scrap_freelancerr_data"),
    path('freelancer/result/', freelancer_result, name="freelancerr_result"),
    path('freelancer/verify/', verify_freelancer_url, name="verify_freelancerr_url"),
    
    path("api/subcategories/<slug:category_slug>/", get_subcategories, name="api-subcategories-f"),
]