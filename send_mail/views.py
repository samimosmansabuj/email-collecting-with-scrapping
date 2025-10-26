from django.shortcuts import render
from django.http import JsonResponse
from .utils import EmailCheck
from .models import EmailConfig, EmailAttachment, EmailTemplateContent
from fiverr.models import FiverrReviewListWithEmail
from freelancerr.models import FreelancerReviewListWithEmail
from core.models import Category, SubCategory
from smtplib import SMTP
from email.mime.text import MIMEText
from django.views import View
import requests
from itertools import chain
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import render_to_string

class Emaillist(View):
    def apply_filters(self, qs, q, country, proficiency, category, sub_category, repeated):
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(username__icontains=q))
        if country: qs = qs.filter(country=country)
        if proficiency: qs = qs.filter(proficiency=proficiency)
        if category: qs = qs.filter(category=category)
        if sub_category: qs = qs.filter(sub_category=sub_category)
        if repeated in ("0", "1"): qs = qs.filter(repeated=bool(int(repeated)))
        return qs
    
    def get_marged_list(self):
        q           = (self.request.GET.get('q') or '').strip()
        country     = self.request.GET.get('country') or ''
        proficiency = self.request.GET.get('proficiency') or ''
        category    = self.request.GET.get('category') or ''
        sub_category = self.request.GET.get('sub_category') or ''
        repeated    = self.request.GET.get('repeated')

        fiverr = self.apply_filters(FiverrReviewListWithEmail.objects.all(), q, country, proficiency, category, sub_category, repeated)
        freelancer = self.apply_filters(FreelancerReviewListWithEmail.objects.all(), q, country, proficiency, category, sub_category, repeated)
        
        marged_list = list(chain(fiverr, freelancer))
        marged_list.sort(key=lambda o: getattr(o, 'created_at', None) or getattr(o, 'id'), reverse=True)
        return marged_list
    
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page') or 1
        per_page    = int(request.GET.get('per_page') or 20)
        category = Category.objects.all()
        if request.GET.get('category') is not None:
            sub_category = SubCategory.objects.filter(category_id=request.GET.get('category'))
        else:
            sub_category = SubCategory.objects.all()
        all_list = self.get_marged_list()
        
        has_filters = any(request.GET.get(k) not in (None, '') for k in
                      ['q','country','price_tag','proficiency','category','sub_category','repeated'])
        paginator = Paginator(all_list, per_page)
        page_obj = paginator.get_page(page_number)
        
        wants_partial = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('partial') == '1'
        if wants_partial:
            rows_html = render_to_string("send_mail/partials/_email_rows.html", {"data_list": page_obj.object_list})
            pagination_html = render_to_string("send_mail/partials/_pagination.html", {
                "page_obj": page_obj,
                "request": request,  # needed to rebuild querystring
            })
            return JsonResponse({
                "rows_html": rows_html,
                "pagination_html": pagination_html,
                "count": paginator.count,
                "has_filters": has_filters,
            })

        context = {
            "data_list": page_obj.object_list,
            "count": paginator.count,
            "has_filters": has_filters,
            "page_obj": page_obj,
            "countries": FiverrReviewListWithEmail.objects.values_list("country", flat=True).distinct().union(
                FreelancerReviewListWithEmail.objects.values_list("country", flat=True).distinct().order_by("country")
            ),
            "proficiencies": FiverrReviewListWithEmail.objects.values_list("proficiency", flat=True).distinct().union(
                FreelancerReviewListWithEmail.objects.values_list("proficiency", flat=True).distinct().order_by("proficiency")
            ),
            "categories": category,
            "sub_categories": sub_category,
            
        }
        
        return render(request, "send_mail/email_list.html", context)


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

