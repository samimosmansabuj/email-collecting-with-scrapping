from django.urls import path
from .views import fiverr_data, ScrapFiverrDataView, result, verify_fiverr_url

urlpatterns = [
    path('fiverr/data-list/', fiverr_data, name="fiverr_data"),
    path('fiverr/scrap-new-data/', ScrapFiverrDataView.as_view(), name="scrap_fiverr_data"),
    path('fiverr/result/', result, name="result"),
    path('fiverr/verify/', verify_fiverr_url, name="verify_fiverr_url"),
]