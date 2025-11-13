from django.urls import path
from .views import single_mail_check, Emaillist, SendEmailFilteringList, EmailSendWithServer, EmailTrackingList, EmailTemplateView, emailtTemplateAction

urlpatterns = [
    path("email/check/", single_mail_check, name="single_mail_check"),
    path("email/list/", Emaillist.as_view(), name="email_list"),
    path("email/send-email/", SendEmailFilteringList.as_view(), name="collection_email_send_multiple"),
    path("email/email-tracking-list/", EmailTrackingList.as_view(), name="email_tracking_list"),
    path("email/send-email-manual/", EmailSendWithServer.as_view(), name="send_mail_manual"),
    
    path("email/template/", EmailTemplateView.as_view(), name="email_template"),
    path("email/template/action/<int:id>/<int:action>/", emailtTemplateAction, name="email_template_action"),
]