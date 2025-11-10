from django.shortcuts import render
from django.http import JsonResponse
from .utils import EmailCheck
from .models import EmailConfig, EmailAttachment, EmailTemplateContent
from fiverr.models import FiverrReviewListWithEmail
from freelancerr.models import FreelancerReviewListWithEmail
from core.models import Category, SubCategory
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from django.views import View
from itertools import chain
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import render_to_string
from core.model_select_choice import EmailTemplatetype
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import deque
from core.utils import AllListMarge
from core.model_select_choice import MailConfigType
import random
import re
from .models import EmailConfig
import time
import requests
import os

class Emaillist(LoginRequiredMixin, View):
    def apply_filters(self, qs, q, country, proficiency, category, sub_category, repeated, send_mail):
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(username__icontains=q))
        if country: qs = qs.filter(country=country)
        if proficiency: qs = qs.filter(proficiency=proficiency)
        if category: qs = qs.filter(category__slug=category)
        if sub_category: qs = qs.filter(sub_category__slug=sub_category)
        if repeated in ("0", "1"): qs = qs.filter(repeated=bool(int(repeated)))
        if send_mail in ("0", "1"): qs = qs.filter(send_mail=bool(int(send_mail)))
        return qs
    
    def get_marged_list(self):
        q           = (self.request.GET.get('q') or '').strip()
        country     = self.request.GET.get('country') or ''
        proficiency = self.request.GET.get('proficiency') or ''
        category    = self.request.GET.get('category') or ''
        sub_category = self.request.GET.get('sub_category') or ''
        repeated    = self.request.GET.get('repeated')
        send_mail    = self.request.GET.get('send_mail')
        
        fiverr = self.apply_filters(FiverrReviewListWithEmail.objects.all(), q, country, proficiency, category, sub_category, repeated, send_mail)
        freelancer = self.apply_filters(FreelancerReviewListWithEmail.objects.all(), q, country, proficiency, category, sub_category, repeated, send_mail)
        
        marged_list = list(chain(fiverr, freelancer))
        marged_list.sort(key=lambda o: getattr(o, 'created_at', None) or getattr(o, 'id'), reverse=True)
        return marged_list
    
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page') or 1
        per_page    = int(request.GET.get('per_page') or 20)
        all_list = self.get_marged_list()
        
        has_filters = any(request.GET.get(k) not in (None, '') for k in
                      ['q','country','price_tag','proficiency','category','sub_category','repeated', 'page'])
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
            "categories": Category.objects.all()            
        }
        
        return render(request, "send_mail/email_list.html", context)

def single_mail_check(request):
    if request.method == "POST":
        email = request.POST.get("email")
        email_check = EmailCheck(email)
        status, msg = email_check.full_email_check()
        return JsonResponse({"status": status, "message": msg})
    return render(request, "mail_verification/mail_check.html")

class SendEmailFilteringList(LoginRequiredMixin, View):
    success = 0
    failed = 0
    cancel = 0
    
    def render_block(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return ""
        paras = re.split(r"\r?\n\s*\r?\n", t)
        html = []
        for p in paras:
            html.append(f"<p>{p.strip().replace('\r', '').replace('\n', '<br>')}</p>")
        return "\n".join(html)
    
    def replace_service_name(self, text: str, service=None, name=None, email=None) -> str:
        text = text or ""

        if name is not None:
            text = re.sub(r"\[\s*my_name\s*\]", str(name), text, flags=re.IGNORECASE)
        if service is not None:
            text = re.sub(r"\[\s*category_name\s*\]", str(service), text, flags=re.IGNORECASE)
        if email is not None:
            text = re.sub(r"\[\s*my_email\s*\]", str(email), text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def validate_hooks(self, header_hook, content_hook, footer_hook, signature_hook):
        hooks = {
            "header_hook": header_hook,
            "content_hook": content_hook,
            "footer_hook": footer_hook,
            "signature_hook": signature_hook,
        }

        for name, value in hooks.items():
            if value is None or len(str(value).split()) < 15:
                raise ValueError(f"{name} must be at least 15 words (got: {value!r})")

    
    def get_dynamical_block_update(self, email_object, email_server):
        # ---------- normalize recipient ----------
        if email_object:
            email_addr = getattr(email_object, "email", "") or ""
            username = (
                getattr(email_object, "username", None)
                or getattr(email_object, "name", None)
                or (email_addr.split("@")[0] if "@" in email_addr else None)
                or "User"
            )
            sc = getattr(email_object, "sub_category", None)
            sub_category_name = getattr(sc, "name", None) if sc else None
        
        # ---------- fetch templates safely ----------
        hh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.HEADER_HOOK, category=email_object.category).first()
        ch = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.CONTENT_HOOK, category=email_object.category)
        chh = random.choice(list(ch)) if ch.exists() else None
        fh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.FOOTER_HOOK, category=email_object.category).first()
        sh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.SIGNATURE_HOOK, category=email_object.category).first()
        
        def body_or_empty(x): return (getattr(x, "body", "") or "").strip()
        sender_name = getattr(email_server, "name", "") or ""
        sender_email = getattr(email_server, "email", "") or ""
        
        # ---------- replace safely (text may be empty) ----------
        header_hook = self.replace_service_name(body_or_empty(hh), sub_category_name, sender_name, sender_email)
        content_hook = self.replace_service_name(body_or_empty(chh), sub_category_name, sender_name, sender_email)
        footer_hook = self.replace_service_name(body_or_empty(fh), sub_category_name, sender_name, sender_email)
        signature_hook = self.replace_service_name(body_or_empty(sh), sub_category_name, sender_name, sender_email)
        self.validate_hooks(header_hook, content_hook, footer_hook, signature_hook)
        
        if self.is_gmail_smtp(email_server):
            tracking_endpoint = os.getenv("TRACKING_ENDPOINT", "https://emailscraping.mnimedu.com/api/mail-image/")
            html_body = f"""<!DOCTYPE html>
            <html>
            <body style="margin:0;padding:0;">
                <p style="margin:auto;">Hi {username} 👋,</p>
                {header_hook}
                {self.render_block(content_hook)}
                {self.render_block(footer_hook)}
                {self.render_block(signature_hook)}
                <img src="{tracking_endpoint}?email={email_addr}&server={email_server.server}" width="1" height="1" alt="" style="display:block;border:0;outline:0;text-decoration:none;">
            </body>
            </html>"""
        else:
            html_body = f"""Hi {username} 👋,\n{header_hook}\n\n{content_hook if content_hook else ""}\n\n{footer_hook}\n\n{signature_hook}"""

        subject = (getattr(chh, "subject", None) or f"{email_object.sub_category.name} — Update").strip()
        mime_msg = MIMEMultipart('alternative')
        mime_msg['Subject'] = str(Header(subject or "Update", 'utf-8'))
        mime_msg['From'] = sender_email
        mime_msg['To'] = email_addr
        if self.is_gmail_smtp(email_server):
            mime_msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        else:
            mime_msg.attach(MIMEText(html_body, 'plain', 'utf-8'))
        return mime_msg

    def apply_filters(self, qs, country, proficiency, category, sub_category, repeated, send_mail):
        if country: qs = qs.filter(country=country)
        if proficiency: qs = qs.filter(proficiency=proficiency)
        if category: qs = qs.filter(category__slug=category)
        if sub_category: qs = qs.filter(sub_category__slug=sub_category)
        if repeated in ("0", "1"): qs = qs.filter(repeated=bool(int(repeated)))
        if send_mail in ("0", "1"): qs = qs.filter(send_mail=bool(int(send_mail)))
        return qs
    
    def get_marged_list(self, request):
        country      = request.POST.get('country') or None
        proficiency  = request.POST.get('proficiency') or None
        category     = request.POST.get('category') or None
        sub_category = request.POST.get('sub_category') or None
        repeated     = request.POST.get('repeated')
        send_mail    = request.POST.get('send_mail')
        
        fiverr = self.apply_filters(FiverrReviewListWithEmail.objects.all(), country, proficiency, category, sub_category, repeated, send_mail)
        freelancer = self.apply_filters(FreelancerReviewListWithEmail.objects.all(), country, proficiency, category, sub_category, repeated, send_mail)
        
        marged_list = list(chain(fiverr, freelancer))
        marged_list.sort(key=lambda o: getattr(o, 'created_at', None) or getattr(o, 'id'), reverse=True)
        return marged_list
    
    def is_gmail_smtp(self, email_server):
        host = (getattr(email_server, "host", "") or "").lower()
        gmail_smtp = (
            "gmail.com" in host or
            host.endswith("gmail.com") or
            host.endswith("googlemail.com")
        )
        return gmail_smtp
    
    def post(self, request, *args, **kwargs):
        try:
            # dummy_list = ["shawon.quantumedge@gmail.com", "	imtiaz.quantumdev@gmai.com", "jewelhfahim@gmail.com", "samim.o.sabuj03@gmail.com", "samim.o.sabuj02@gmail.com", "samim.o.sabuj01@gmail.com", "rajibhasanshawon@gmail.com"]
            # marge_data = FiverrReviewListWithEmail.objects.filter(email__in=dummy_list)[:1]
            marge_data = self.get_marged_list(request)
            print("Total Data: >>>", len(marge_data), "<<<")
            
            # email_servers = deque(list(EmailConfig.objects.filter(server__in=["gmail_samim"])))
            email_servers = deque(list(EmailConfig.objects.filter(is_active=True, is_default=True, today_complete=False)))
            random.shuffle(email_servers)
            if not email_servers:
                return JsonResponse({"status": "error", "message": "Not Email Server Available!"}, status=400)
            
            email_send_at_a_time = int(os.getenv("SEND_MAIL_AT_A_TIME"))
            total_mailsend_available = len(email_servers) * email_send_at_a_time
            print("Total Email Server Exist: ", len(email_servers))
            print("Total Send Mail Start: >>>", total_mailsend_available, "<<<")
            
            loop = 1
            for email_object in marge_data[:total_mailsend_available]:
                # self.success += 1
                # print("*****************************************************************************************************")
                # print("Email Object: ", email_object)
                # print("Category: ", email_object.category)
                # email_server = email_servers[0]
                # print("Email Server: ", email_server)
                # print("Template: ", self.get_dynamical_block_update(email_object, email_server))
                # email_servers.rotate(-1)
                # print("*****************************************************************************************************")
                
                time.sleep(1)
                print(f"****************************************--#{loop} Start--***************************************************")
                attempts = 0
                last_exc = None
                while attempts < len(email_servers):
                    email_server = email_servers[0]
                    try:
                        print(f"Connect to Mail Server  >>> {email_server}")
                        server = SMTP(email_server.host, email_server.port)
                        server.starttls()
                        server.login(email_server.host_user, email_server.host_password)
                        print(f"Server Connected  >>> {email_server}")
                        break
                    except Exception as e:
                        last_exc = e
                        print(f"Failed {str(e)} with {email_server}. Trying another...")
                        email_servers.rotate(-1)
                        attempts += 1
                else:
                    print(f"All servers failed for {email_object}. Last error: {last_exc}")
                    self.failed += 1
                time.sleep(1)
                try:
                    print("Template Generate Processing......")
                    msg = self.get_dynamical_block_update(email_object, email_server)
                    print("Template Generate Complete!")
                    
                    print(f"Email Sending to {email_object.email}...")
                    server.sendmail(
                        from_addr=email_server.email, to_addrs=email_object.email, msg=msg.as_string()
                    )
                    print(f"Email sent to '{email_object.email}' successfully!")
                    
                    self.success += 1
                    email_object.send_mail = True
                    if self.is_gmail_smtp(email_server): email_object.last_event = "delivered"
                    email_object.last_mail_server = email_server
                    email_object.last_sent_at = timezone.now()
                    email_object.save()
                    server.quit()
                    print("Server Disconnected!")
                    email_servers.rotate(-1)
                except Exception as e:
                    print(f"Failed to Sending Email: {str(e)}")
                    # email_servers.rotate(-1)
                    self.failed += 1
                print("*****************************************************************************************************")
                time.sleep(1)
                loop += 1
            
            status_count = {
                "success": self.success,
                "failed": self.failed,
                "cancel": self.cancel
            }
            print("status_count: ", status_count)
            return JsonResponse({
                "status": "ok",
                "processed": len(marge_data),
                "message": f"Mail sent to {len(marge_data)} item(s)."
            })
        except Exception as e:
            print("eeee:", str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

class EmailSendWithServer(View):
    def get(self, request, *args, **kwargs):
        mail_server = EmailConfig.objects.filter(is_active=True)
        return render(request, "send_mail/mail_send_manual.html", {"mail_server": mail_server})
    
    def replace_service_name(self, text: str, service=None, name=None, email=None) -> str:
        text = text or ""
        if name is not None:
            text = re.sub(r"\[\s*my_name\s*\]", str(name), text, flags=re.IGNORECASE)
        if service is not None:
            text = re.sub(r"\[\s*category_name\s*\]", str(service), text, flags=re.IGNORECASE)
        if email is not None:
            text = re.sub(r"\[\s*my_email\s*\]", str(email), text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def render_block(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return ""
        paras = re.split(r"\r?\n\s*\r?\n", t)
        html = []
        for p in paras:
            html.append(f"<p>{p.strip().replace('\r', '').replace('\n', '<br>')}</p>")
        return "\n".join(html)
    
    def get_dynamical_block_update(self, email_object, email_server):
        # ---------- normalize recipient ----------
        if isinstance(email_object, str) and email_object:
            username = (email_object.split("@")[0] or "User").strip()
            sub_category_name = None
            email_addr = email_object
        elif email_object:
            email_addr = getattr(email_object, "email", "") or ""
            username = (
                getattr(email_object, "username", None)
                or getattr(email_object, "name", None)
                or (email_addr.split("@")[0] if "@" in email_addr else None)
                or "User"
            )
            sc = getattr(email_object, "sub_category", None)
            sub_category_name = getattr(sc, "name", None) if sc else None
        else:
            username = "User"
            sub_category_name = None
            email_addr = ""
        
        # ---------- fetch templates safely ----------
        hh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.HEADER_HOOK).first()
        ch = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.CONTENT_HOOK)
        chh = random.choice(list(ch)) if ch.exists() else None
        fh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.FOOTER_HOOK).first()
        sh = EmailTemplateContent.objects.filter(is_active=True, type=EmailTemplatetype.SIGNATURE_HOOK).first()
        
        def body_or_empty(x): return (getattr(x, "body", "") or "").strip()
        sender_name = getattr(email_server, "name", "") or ""
        sender_email = getattr(email_server, "email", "") or ""
        
        # ---------- replace safely (text may be empty) ----------
        header_hook = self.replace_service_name(body_or_empty(hh), sub_category_name, sender_name, sender_email)
        content_hook = self.replace_service_name(body_or_empty(chh), sub_category_name, sender_name, sender_email)
        footer_hook = self.replace_service_name(body_or_empty(fh), sub_category_name, sender_name, sender_email)
        signature_hook = self.replace_service_name(body_or_empty(sh), sub_category_name, sender_name, sender_email)
        
        subject = (getattr(chh, "subject", None) or f"{sub_category_name} — Update").strip()
        safe_tracker_email = email_addr or "unknown@example.com"
        tracking_endpoint = os.getenv("TRACKING_ENDPOINT", "https://emailscraping.mnimedu.com/api/mail-image/")

        msg_body = f"""<!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;">
            <p style="margin:auto;">Hello Dear,</p>
            {header_hook}
            {self.render_block(content_hook)}
            {self.render_block(footer_hook)}
            {self.render_block(signature_hook)}
            <img src="{tracking_endpoint}?email={safe_tracker_email}&server={email_server.server}" width="1" height="1" alt="" style="display:block;border:0;outline:0;text-decoration:none;">
        </body>
        </html>"""
        return msg_body, subject if chh else None, email_addr
    
    def is_gmail_smtp(self, email_server):
        host = (getattr(email_server, "host", "") or "").lower()
        gmail_smtp = (
            "gmail.com" in host or
            host.endswith("gmail.com") or
            host.endswith("googlemail.com")
        )
        return gmail_smtp
    
    def post(self, request, *args, **kwargs):
        server = request.POST.get('mail_server')
        mail_body = request.POST.get('mail_body')
        emailInput = request.POST.get('email')
        self.emailaddress = emailInput
        print("*******************************************************")
        email_object = AllListMarge.search_by_email(email=emailInput)
        if not email_object:
            email_only = emailInput
        
        try:
            mail_server = EmailConfig.objects.get(server=server)
        except EmailConfig.DoesNotExist:
            print("*******************************************************")
            return JsonResponse({"ok": False, "message": "Host not found"}, status=404)
        
        # url = "https://smtp.maileroo.com/api/v2/emails"
        # api_key = "14ef21382229e376e614697dec77e7b58c390c294161662499c18e4ad3980175"
        # html_body, subject, email_addr = self.get_dynamical_block_update(email_object or email_only, mail_server)
        # payload = {
        #     "from": {"address": mail_server.email, "display_name": "Samim Osman"},
        #     "to": [{"address": emailInput, "display_name": "Samim Osman"}],
        #     "reply_to": {"address": "samim.quantumdev@gmail.com","display_name": "Samim Osman"},
        #     "subject": subject,
        #     "html": html_body,
        #     "plain": html_body,
        #     "tracking": True
        # }
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Bearer {api_key}"
        # }
        # response = requests.post(url=url, json=payload, headers=headers)
        # print(response.status_code, response.json())
        # print("*******************************************************")
        # return JsonResponse({"ok": True, "message": "Mail Send Successfully!"})
        
        if mail_server.type == MailConfigType.API:
            api_key = mail_server.api_key
            url = "https://connect.mailerlite.com/api"
            # url = "https://api.mailerlite.com/api/v2"
            header = {
                "Authorization": f"Bearer {mail_server.api_key}"
            }
            res = requests.post(url=url, headers=header)
            try:
                data = res.json()
            except ValueError:
                print("Response is not JSON! Here's what came:")
                print(res.text)
            print("res: ", data)
            return JsonResponse({"ok": False, "message": "Ok"}, status=404)
        else:
            try:
                html_body, subject, email_addr = self.get_dynamical_block_update(email_object or email_only, mail_server)
                if not email_addr:
                    raise ValueError("No recipient email found")
                
                mime_msg = MIMEMultipart('alternative')
                mime_msg['Subject'] = str(Header(subject or "Update", 'utf-8'))
                mime_msg['From'] = formataddr((mail_server.name, mail_server.email))
                mime_msg['To'] = email_addr
                mime_msg["Reply-To"] = formataddr(("Samim Osman", "samim.quantumdev@gmail.com"))
                mime_msg.attach(MIMEText(html_body, 'html', 'utf-8'))

                print(f"Connect to Mail Server  >>> {mail_server}")
                server = SMTP(host=mail_server.host, port=mail_server.port)
                server.starttls()
                server.login(mail_server.host_user, mail_server.host_password)
                print("Mail Server Connected!")
                print(f"Mail Sending to {email_addr}...")
                server.sendmail(
                    from_addr=mail_server.email, to_addrs=email_addr, msg=mime_msg.as_string()
                )
                
                if email_object is object:
                    email_object.send_mail = True
                    email_object.last_mail_server = mail_server
                    if self.is_gmail_smtp(mail_server): email_object.last_event = "delivered"
                    email_object.last_sent_at = timezone.now()
                    email_object.save()
                
                print(f"Email sent to '{emailInput}' successfully!")
                print("*******************************************************")
                return JsonResponse({"ok": True, "message": "Mail Send Successfully!"})
            except Exception as e:
                print("*******************************************************")
                return JsonResponse({"ok": False, "message": str(e)}, status=404)

class EmailTrackingList(LoginRequiredMixin, View):
    def apply_filters(self, qs, q, country, last_mail_server, category, sub_category, event):
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(username__icontains=q))
        if country: qs = qs.filter(country=country)
        if last_mail_server: qs = qs.filter(last_mail_server=last_mail_server)
        if category: qs = qs.filter(category__slug=category)
        if sub_category: qs = qs.filter(sub_category__slug=sub_category)
        if event:
            if event == "None":
                qs = qs.filter(last_event__isnull=True)
            else:
                qs = qs.filter(last_event=event)
        return qs
    
    def get_mail_server(self, id):
        try:
            return EmailConfig.objects.get(id=id)
        except:
            return None
    
    def get_marged_list(self):
        q           = (self.request.GET.get('q') or '').strip()
        country     = self.request.GET.get('country') or ''
        last_mail_server_id = self.request.GET.get('last_mail_server') or ''
        last_mail_server = self.get_mail_server(last_mail_server_id)
        category    = self.request.GET.get('category') or ''
        sub_category = self.request.GET.get('sub_category') or ''
        event    = self.request.GET.get('event')
        fiverr = self.apply_filters(FiverrReviewListWithEmail.objects.filter(send_mail=True), q, country, last_mail_server, category, sub_category, event)
        freelancer = self.apply_filters(FreelancerReviewListWithEmail.objects.filter(send_mail=True), q, country, last_mail_server, category, sub_category, event)
        
        marged_list = list(chain(fiverr, freelancer))
        marged_list.sort(key=lambda o: getattr(o, 'created_at', None) or getattr(o, 'id'), reverse=True)
        return marged_list
    
    def is_gmail_smtp(self, email_server):
        host = (getattr(email_server, "host", "") or "").lower()
        gmail_smtp = (
            "gmail.com" in host or
            host.endswith("gmail.com") or
            host.endswith("googlemail.com")
        )
        return gmail_smtp
    
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page') or 1
        per_page    = int(request.GET.get('per_page') or 20)
        all_list = self.get_marged_list()
        
        has_filters = any(request.GET.get(k) not in (None, '') for k in
                      ['q','country','last_mail_server','category','sub_category', 'last_event', 'page'])
        paginator = Paginator(all_list, per_page)
        page_obj = paginator.get_page(page_number)
        
        wants_partial = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('partial') == '1'
        if wants_partial:
            rows_html = render_to_string("send_mail/trakcing_email/_email_rows.html", {"data_list": page_obj.object_list})
            pagination_html = render_to_string("send_mail/trakcing_email/_pagination.html", {
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
            "countries": FiverrReviewListWithEmail.objects.filter(send_mail=True).values_list("country", flat=True).distinct().union(
                FreelancerReviewListWithEmail.objects.filter(send_mail=True).values_list("country", flat=True).distinct().order_by("country")
            ),
            "last_events": FiverrReviewListWithEmail.objects.values_list("last_event", flat=True).distinct().union(
                FreelancerReviewListWithEmail.objects.values_list("last_event", flat=True).distinct().order_by("last_event")
            ),
            "last_mail_servers": EmailConfig.objects.all(),
            "categories": Category.objects.all()            
        }
        
        return render(request, "send_mail/trakcing_email/tracking_email_list.html", context)



