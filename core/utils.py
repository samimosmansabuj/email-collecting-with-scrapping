import re
import smtplib
import socket
import dns.resolver
from django.utils.text import slugify

class EmailGenerate:
    def __init__(self, email):
        self.email = email
    
    def is_valid_syntax(self, email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    def has_mx_record(self, domain):
        try:
            records = dns.resolver.resolve(domain, 'MX')
            return [str(r.exchange) for r in records]
        except Exception:
            return []
    
    def smtp_check(self, email):
        try:
            domain = email.split('@')[1]
            mx_records = self.has_mx_record(domain)
            if not mx_records:
                return False, "❌ No MX record found"

            mx_host = mx_records[0]
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host)
            server.helo(socket.gethostname())
            server.mail("check@example.com")
            code, message = server.rcpt(email)
            server.quit()
            return code, f"{code} {message.decode() if isinstance(message, bytes) else message}"

        except Exception as e:
            return False, f"Error: {e}"

    def full_email_check(self):
        email = self.email
        
        if not self.is_valid_syntax(email):
            msg = f"{email} => ❌ Invalid email format"
            return False, msg

        domain = email.split('@')[1]
        mx_records = self.has_mx_record(domain)

        if not mx_records:
            msg = f"{email} => ❌ Domain not valid (no MX records)"
            return False, msg, 350

        code, msg = self.smtp_check(email)
        if (code in (250, 251)):
            msg = f"{email} => ✅ Email exists (SMTP verified)"
            return True, msg, code
        else:
            msg = f"{email} => ⚠️ Domain valid, but SMTP check failed ({msg})"
            return False, msg, code


def generate_unique_slug(model_object, field_value, old_slug=None):
    slug = slugify(field_value)
    if slug != old_slug:
        unique_slug = slug
        num = 1
        while model_object.objects.filter(slug=unique_slug).exists():
            if unique_slug == old_slug:
                return old_slug
            unique_slug = f'{slug}-{num}'
            num+=1
        return unique_slug
    else:
        return old_slug


