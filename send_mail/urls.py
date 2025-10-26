from django.urls import path
from .views import single_mail_check, Emaillist, EmailSending

urlpatterns = [
    path("email/check/", single_mail_check, name="single_mail_check"),
    path("email/list/", Emaillist.as_view(), name="email_list"),
    path("email/send-email/", EmailSending.as_view(), name="send_mail")
]