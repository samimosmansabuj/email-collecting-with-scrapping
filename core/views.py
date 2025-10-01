from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from fiverr.models import ReviewListWithEmail

BUSINESS_NAME = "PyTeam"
BUSINESS_DESC = ("AI Based Automation Software Company. Mainly using Python but we provide all kinds "
                 "of software, graphics, animation, automation and AI solutions with all programming languages.")


def home(request):
    return render(request, 'home.html', {'business_name': BUSINESS_NAME, 'business_description': BUSINESS_DESC})



@login_required
def dashboard(request):
    total_scrapping = ReviewListWithEmail.objects.all().count()
    return render(request, 'dashboard.html', {'total_scrapping': total_scrapping})

def logoutview(request):
    logout(request)
    return redirect("home_page")
