from django.shortcuts import render
from django.http import JsonResponse
from .utils import EmailCheck

def single_mail_check(request):
    if request.method == "POST":
        email = request.POST.get("email")
        email_check = EmailCheck(email)
        status, msg = email_check.full_email_check()
        return JsonResponse({"status": status, "message": msg})
    return render(request, "mail_verification/mail_check.html")


def send_mail(request):
    return JsonResponse({"status": True, "health": True})

