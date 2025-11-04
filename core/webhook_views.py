from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.conf import settings
from .models import WebhookEventLogs, WebHookServer, EmailOpenLog
from core.utils import AllListMarge
from .utils import _ts_to_dt
from django.utils import timezone
import json
import base64

@require_POST
@csrf_exempt
def webhook_events_log_views(request, server):
    EVENTS = {
        "delivered", "hard_bounce", "soft_bounce",
        "blocked", "spam", "invalid_email", "deferred", "click", "error", "clicked",
        "opened", "unique_opened", "unsubscribed", "proxy_open", "unique_proxy_open"
    }
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    if server == WebHookServer.BREVO:
        WebhookEventLogs.objects.create(webhook_json=payload, server=WebHookServer.BREVO)
        payload = payload
    if server == WebHookServer.MAILEROO:
        WebhookEventLogs.objects.create(webhook_json=payload, server=WebHookServer.MAILEROO)
        event_data = payload.get("event_data")
    
    event = payload.get("event") or payload.get("event_type")
    email_data = payload.get("email") or event_data.get("to") or ""
    if isinstance(email_data, list):
        email_data = email_data[0]
    email = str(email_data).strip().lower()
    ts_event = payload.get("ts_event") or payload.get("ts") or payload.get("event_time")
    dt = _ts_to_dt(ts_event) if ts_event else None
    
    if not email or event not in EVENTS:
        return HttpResponseBadRequest("missing/invalid fields")
    
    email_object = AllListMarge.search_by_email(email=email)
    if not email_object:
        return JsonResponse({"ok": True, "found": False})
    
    if email_object.last_provider_ts and ts_event and int(ts_event) <= int(email_object.last_provider_ts):
        return JsonResponse({"ok": True, "skipped": "old_event"})
    
    email_object.last_event = event
    if dt and not settings.USE_TZ and timezone.is_aware(dt):
        dt = timezone.make_naive(dt)
    email_object.last_event_at = dt
    
    if ts_event:
        email_object.last_provider_ts = int(ts_event)
    email_object.save()
    print(f"webhook ok for : {email}", True)
    return JsonResponse({
        "ok": True,
        "event": event,
        "email": email,
        "found": bool(email_object),
        "id": getattr(email_object, "id", None),
    })



PIXEL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
    "ASsJTYQAAAAASUVORK5CYII="
)
PIXEL_BYTES = base64.b64decode(PIXEL_PNG_B64)
# @require_GET
def gmail_tracking_api(request):
    print("Email tracking Webhook response!")
    resp = HttpResponse(PIXEL_BYTES, content_type="image/png", status=200)
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    
    email = request.GET.get("email", "")
    server = request.GET.get("server", "")
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    try:
        email_object = AllListMarge.search_by_email(email=email)
        if EmailOpenLog.objects.filter(email=email).exists():
            emailopenlog = EmailOpenLog.objects.get(email=email)
            last_event = "opened"
            emailopenlog.open_count += 1
            emailopenlog.opened_at=timezone.now()
            emailopenlog.mail_server_name=server
            emailopenlog.save()
        else:
            EmailOpenLog.objects.create(email=email, ip=ip, opened_at=timezone.now(), mail_server_name=server, open_count=1)
            last_event = "unique_opened"
        
        email_object.last_event = last_event
        email_object.last_event_at = timezone.now()
        email_object.save() 
    except Exception as e:
        print("e: ", e)
        print("email: ", email)
    return resp


