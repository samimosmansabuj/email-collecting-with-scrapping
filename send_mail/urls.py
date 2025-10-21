from django.urls import path
from .views import single_mail_check, send_mail

urlpatterns = [
    path("email/check/", single_mail_check, name="single_mail_check"),
    path("email/send-email/", send_mail, name="send_mail")
]