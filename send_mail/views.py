from django.shortcuts import render
from django.http import JsonResponse
from .utils import EmailCheck
from .models import EmailConfig, EmailAttachment, EmailTemplateContent
from smtplib import SMTP
from email.mime.text import MIMEText

def single_mail_check(request):
    if request.method == "POST":
        email = request.POST.get("email")
        email_check = EmailCheck(email)
        status, msg = email_check.full_email_check()
        return JsonResponse({"status": status, "message": msg})
    return render(request, "mail_verification/mail_check.html")


def send_mail(request):
    config_email = EmailConfig.objects.all().first()
    template = EmailTemplateContent.objects.first()

    # msg=MIMEText(template.body).as_string()
    msg=MIMEText(template.body)
    msg['Subject'] = template.subject
    msg['From'] = config_email.email
    msg['To'] = "samim.o.sabuj01@gmail.com"

    try:
        server = SMTP(config_email.host, config_email.port)
        server.starttls()
        server.login(config_email.email, config_email.host_password)

        server.sendmail(
            from_addr=config_email.email, to_addrs=["samim.o.sabuj01@gmail.com"], msg=msg.as_string()
        )
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()

    return JsonResponse({"status": True, "health": True})

