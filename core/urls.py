from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *
from .webhook_views import *

urlpatterns = [
    path('', home, name='home_page'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logoutview, name='logout'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('dashboard/', dashboard, name='dashboard'),

    
    path("api/subcategories/<slug:category_slug>/", get_subcategories, name="api-subcategories"),
    path("api/get-mail-server/<slug:server>/", get_mail_server, name="api-get_mail_server"),
    path("api/fiverr-url-verify/", verified_fiverr_url, name="api-fiverrurlverify"),
    
    #Brevo Mail Status Webhook
    path("api/webhook/<str:server>/", webhook_events_log_views, name="brevo_email_status_webhook"),
    path("api/mail-image/", gmail_tracking_api, name="gmail_tracking_api"),
]
