from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from fiverr.models import FiverrReviewListWithEmail, FiverrCompleteGigDetails
from freelancerr.models import FreelancerReviewListWithEmail
from django.views.decorators.http import require_POST, require_GET
from .models import Category, SubCategory
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
        print("data: ", data)
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

