from django.urls import path
from .views import single_mail_check, Emaillist, SendFilteringListEmail, EmailSendWithServer

urlpatterns = [
    path("email/check/", single_mail_check, name="single_mail_check"),
    path("email/list/", Emaillist.as_view(), name="email_list"),
    path("email/send-email/", SendFilteringListEmail.as_view(), name="collection_email_send_multiple"),
    path("email/send-email-manual/", EmailSendWithServer.as_view(), name="send_mail_manual")
]