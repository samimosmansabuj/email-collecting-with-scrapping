from django.urls import path
from .views import fiverr_data, ScrapFiverrDataView, result

urlpatterns = [
    path('fiverr/data-list/', fiverr_data, name="fiverr_data"),
    path('fiverr/scrap_new_data/', ScrapFiverrDataView.as_view(), name="scrap_fiverr_data"),
    path('fiverr/result/', result, name="result"),
]