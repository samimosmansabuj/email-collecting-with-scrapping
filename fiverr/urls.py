from django.urls import path
from .views import fiverr_data, ScrapFiverrDataView, result, get_subcategories, verify_fiverr_url

urlpatterns = [
    path('fiverr/data-list/', fiverr_data, name="fiverr_data"),
    path('fiverr/scrap_new_data/', ScrapFiverrDataView.as_view(), name="scrap_fiverr_data"),
    path('fiverr/result/', result, name="result"),
    path('fiverr/verify/', verify_fiverr_url, name="verify_fiverr_url"),
    
    # path("get-sub-category/<str:category_slug>/", get_subcategory, name="get_subcategory"),
    path("api/subcategories/<slug:category_slug>/", get_subcategories, name="api-subcategories"),
]