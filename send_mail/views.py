from django.shortcuts import render
from django.http import JsonResponse
from .utils import EmailCheck
from .models import EmailConfig, EmailAttachment, EmailTemplateContent
from smtplib import SMTP
from email.mime.text import MIMEText
from django.views import View
import requests

class Emaillist(View):
    def get(self, request, *args, **kwargs):
        return render(request, "send_mail/email_list.html")


def single_mail_check(request):
    if request.method == "POST":
        email = request.POST.get("email")
        email_check = EmailCheck(email)
        status, msg = email_check.full_email_check()
        return JsonResponse({"status": status, "message": msg})
    return render(request, "mail_verification/mail_check.html")

def send_mail(request):
    template = EmailTemplateContent.objects.first()
    
    proxy_host = request.GET.get("proxy_host")
    if proxy_host == "brevo":
        # msg=MIMEText(template.body).as_string()
        msg=MIMEText(template.body)
        msg['Subject'] = template.subject
        msg['From'] = "samim.quantumdev@gmail.com"
        msg['To'] = "samim.o.sabuj01@gmail.com"

        try:
            server = SMTP("smtp-relay.brevo.com", 587)
            server.starttls()
            server.login("989996001@smtp-brevo.com", "YfIOqJDQBXbjMVEg")

            server.sendmail(
                from_addr="samim.quantumdev@gmail.com", to_addrs=["samim.o.sabuj01@gmail.com"], msg=msg.as_string()
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()
    elif proxy_host == "mailersend":
        msg=MIMEText(template.body)
        msg['Subject'] = template.subject
        msg['From'] = "samim.quantumdev@gmail.com"
        msg['To'] = "nusrat.j.fatema@gmail.com"

        try:
            server = SMTP("smtp.mailersend.net", 587)
            server.starttls()
            server.login("MS_J69WpO@test-86org8erre1gew13.mlsender.net", "mssp.74YkC1c.pq3enl69578l2vwr.dUt8Jg1")

            server.sendmail(
                from_addr="samim.quantumdev@gmail.com", to_addrs=["nusrat.j.fatema@gmail.com"], msg=msg.as_string()
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()
    elif proxy_host == "mailgun":
        msg=MIMEText(template.body)
        msg['Subject'] = template.subject
        msg['From'] = "samim.quantumdev@gmail.com"
        msg['To'] = "nusrat.j.fatema@gmail.com"

        try:
            server = SMTP("smtp.mailersend.net", 587)
            server.starttls()
            server.login("MS_J69WpO@test-86org8erre1gew13.mlsender.net", "mssp.74YkC1c.pq3enl69578l2vwr.dUt8Jg1")

            server.sendmail(
                from_addr="samim.quantumdev@gmail.com", to_addrs=["nusrat.j.fatema@gmail.com"], msg=msg.as_string()
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()
    elif proxy_host == "turbo-smtp":
        url = "https://api.turbo-smtp.com/api/v2/mail/send"
        body = {
            "authuser": "samim.quantumdev@gmail.com",
            "authpass": "SafaPrincess@16",
            "from": "samim.quantumdev@gmail.com",
            "to": "nusrat.j.fatema@gmail.com",
            "subject": "This is a test message",
            "cc": "samim.quantumdev@gmail.com",
            "bcc": "samim.quantumdev@gmail.com",
            "content": "This is plain text version of the message.",
            "html_content": "This is <b>HTML</b> version of the message."
        }
        res = requests.post(url=url, json=body)
        print("res.json(): ", res.json())
    elif proxy_host == "mailjet":
        msg=MIMEText(template.body)
        msg['Subject'] = template.subject
        msg['From'] = "samim.quantumdev@gmail.com"
        msg['To'] = "nusrat.j.fatema@gmail.com"

        try:
            server = SMTP("smtp.mailersend.net", 587)
            server.starttls()
            server.login("MS_J69WpO@test-86org8erre1gew13.mlsender.net", "mssp.74YkC1c.pq3enl69578l2vwr.dUt8Jg1")

            server.sendmail(
                from_addr="samim.quantumdev@gmail.com", to_addrs=["nusrat.j.fatema@gmail.com"], msg=msg.as_string()
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()

        # try:
        #     server = SMTP("pro.turbo-smtp.com", 465)
        #     server.starttls()
        #     server.login("samim.quantumdev@gmail.com", "TP1UthNY")

        #     server.sendmail(
        #         from_addr="samim.quantumdev@gmail.com", to_addrs=["nusrat.j.fatema@gmail.com"], msg=msg.as_string()
        #     )
        #     print("Email sent successfully!")
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        # finally:
        #     server.quit()
    else:
        print("No Use Any Server for Sending Email")
    return JsonResponse({"status": True, "health": True})

# def send_mail(request):
#     config_email = EmailConfig.objects.all().first()
#     template = EmailTemplateContent.objects.first()

#     # msg=MIMEText(template.body).as_string()
#     msg=MIMEText(template.body)
#     msg['Subject'] = template.subject
#     msg['From'] = config_email.email
#     msg['To'] = "samim.o.sabuj01@gmail.com"

#     try:
#         server = SMTP(config_email.host, config_email.port)
#         server.starttls()
#         server.login(config_email.host_user, config_email.host_password)

#         server.sendmail(
#             from_addr=config_email.email, to_addrs=["samim.o.sabuj01@gmail.com"], msg=msg.as_string()
#         )
#         print("Email sent successfully!")
#     except Exception as e:
#         print(f"Error sending email: {e}")
#     finally:
#         server.quit()

#     return JsonResponse({"status": True, "health": True})

