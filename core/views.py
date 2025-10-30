from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from fiverr.models import FiverrReviewListWithEmail, FiverrCompleteGigDetails
from freelancerr.models import FreelancerReviewListWithEmail
from django.views.decorators.http import require_POST, require_GET
from .models import Category, SubCategory
from send_mail.models import EmailConfig
from .utils import AllListMarge, _ts_to_dt
from django.utils import timezone
from django.conf import settings
import json

BUSINESS_NAME = "PyTeam"
BUSINESS_DESC = ("AI Based Automation Software Company. Mainly using Python but we provide all kinds "
                 "of software, graphics, animation, automation and AI solutions with all programming languages.")


def home(request):
    return render(request, 'home.html', {'business_name': BUSINESS_NAME, 'business_description': BUSINESS_DESC})



@login_required
def dashboard(request):
    total_scrapping_1 = FiverrReviewListWithEmail.objects.all().count()
    total_scrapping_2 = FreelancerReviewListWithEmail.objects.all().count()
    return render(request, 'dashboard.html', {'total_scrapping': total_scrapping_1+total_scrapping_2})

def logoutview(request):
    logout(request)
    return redirect("home_page")

@login_required
@require_GET
def get_subcategories(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    subs = SubCategory.objects.filter(category=category).values("id", "name", "slug")
    data = list(subs)
    return JsonResponse({"ok": True, "results": data, "count": len(data)}, status=200)

@login_required
@require_GET
def get_mail_server(request, server):
    try:
        mail_server = EmailConfig.objects.get(server=server)
    except EmailConfig.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Host not found"}, status=404)

    data = {
        "host": mail_server.host,
        "host_user": mail_server.host_user,
        "host_password": mail_server.host_password,
        "port": mail_server.port,
        "tls": mail_server.tls,
    }

    return JsonResponse({"ok": True, "results": data})

# @login_required
@require_POST
@csrf_exempt
def verified_fiverr_url(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            urltype = data.get("type")
            username = data.get("username")
            url = data.get("url")
        except Exception:
            return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)
        if FiverrCompleteGigDetails.objects.filter(username=username, url=url, details_type=urltype).exists():
            data = FiverrCompleteGigDetails.objects.get(username=username, url=url, details_type=urltype)
            return JsonResponse(
                {
                    "ok": True,
                    "message": "Gig/Profile already Scrapping!",
                    "data": {
                        "username": data.username,
                        "url": data.url,
                        "total_reviews": data.total_reviews,
                        "total_scrapping": data.total_scrapping
                    }
                }
            )
        else:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "The Gig/Profile not scrapping!"
                }
            )
    else:
        return JsonResponse({
            "ok": False,
            "message": "Only POST allowed!"
        }, status=405)


@require_POST
@csrf_exempt
def brevo_email_status_webhook(request):
    EVENTS = {
        "request", "delivered", "hard_bounce", "soft_bounce",
        "blocked", "spam", "invalid_email", "deferred", "click", "error",
        "opened", "unique_opened", "unsubscribed", "proxy_open"
    }
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    print("payload: ", payload)
    
    event = payload.get("event", "")
    email = (payload.get("email") or "").strip().lower()
    ts_event = payload.get("ts_event") or payload.get("ts")
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
    
    return JsonResponse({
        "ok": True,
        "event": event,
        "email": email,
        "found": bool(email_object),
        "id": getattr(email_object, "id", None),
    })


# @require_GET
def gmail_tracking_api(request):
    email = request.GET.get("email", "")
    print("email: ", email)
    return JsonResponse({"ok": True, "health": True})
    # try:
    #     email = request.get("email", "")
    #     print("email: ", email)
    #     return JsonResponse({"ok": True, "health": True})
    # except:
    #     return JsonResponse({"ok": False, "health": False})
