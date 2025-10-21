import re
import smtplib
import socket
import dns.resolver

class EmailCheck:
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
    
    def smtp_check(self, email, mx_records):
        try:
            mx_host = mx_records[0]
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host)
            server.helo(socket.gethostname())
            server.mail("check@example.com")
            code, message = server.rcpt(email)
            server.quit()
            return code, f"{code} {message.decode() if isinstance(message, bytes) else message}"
        except Exception as e:
            msg = f"Error: {e}"
            return False, msg

    def full_email_check(self):
        if not self.is_valid_syntax(self.email):
            msg = f"{self.email} => ❌ Invalid email format"
            return False, msg

        mx_records = self.has_mx_record(self.email.split('@')[1])
        if not mx_records:
            msg = f"{self.email} => ❌ Domain not valid (no MX records)"
            return False, msg

        code, msg = self.smtp_check(self.email, mx_records)
        if (code in (250, 251)):
            msg = f"{self.email} => ✅ Email exists (SMTP verified)"
            return True, msg
        elif code is False:
            return False, msg
        else:
            msg = f"{self.email} => ⚠️ Email Invalid, (SMTP failed)"
            return False, msg


