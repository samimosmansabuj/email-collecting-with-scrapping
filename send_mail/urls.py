from django.urls import path
from .views import single_mail_check, send_mail, Emaillist

urlpatterns = [
    path("email/check/", single_mail_check, name="single_mail_check"),
    path("email/list/", Emaillist.as_view(), name="email_list"),
    path("email/send-email/", send_mail, name="send_mail")
]