from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from core.models import InvalidUsernameEmail
from fiverr.models import FiverrReviewListWithEmail
from django.views import View
from bs4 import BeautifulSoup
import time
from core.utils import EmailGenerate
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
import base64

@login_required
def freelancer_data(request):
    data_list = FreelancerReviewListWithEmail.objects.all().order_by("-updated_at")
    return render(request, "freelancerr/data_list.html", {
        "data_list": data_list[:20], "count": len(data_list)
    })

login_required
@require_GET
def get_subcategories(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    subs = SubCategory.objects.filter(category=category).values("id", "name", "slug")
    data = list(subs)
    return JsonResponse({"ok": True, "results": data, "count": len(data)}, status=200)


@method_decorator(login_required, name='dispatch')
class ScrapFreelancerDataView(View):
    template_name = "freelancerr/scrapping_form.html"
    success_count = 0
    not_found_count = 0
    duplicated_count = 0
    failed_count = 0

    def get(self, request, *args, **kwargs):
        context = {}
        context["caregory"] = Category.objects.all()
        return render(request, self.template_name, context)
    
    def username_and_url_check(self, username, url, total_reviews, total_reviews_count):
        if FreelancerCompleteProfileDetails.objects.filter(username = username, url = url).exists():
            get_object = FreelancerCompleteProfileDetails.objects.get(username = username, url = url)
            if int(get_object.total_reviews) == int(total_reviews):
                return True, False # existing, updated
            else:
                get_object.total_update += 1
                get_object.total_reviews = total_reviews
                get_object.total_scrapping = total_reviews_count
                get_object.save()
                return False, True # existing, updated
        return False, False # existing, updated
    
    def scrapping_all_reviews(self, html, urltype):
        soup = BeautifulSoup(html, "html.parser")
        if urltype and urltype.lower() == "profile":
            all_reviews = soup.find_all("div", class_="MainContainer")
        else:
            all_reviews = soup.find_all("div", class_="MainContainer")
        total_reviews_count = len(all_reviews)
        print("Total reviews found:", total_reviews_count)
        return all_reviews, total_reviews_count
    
    def safe_get_text(self, parent, tag, class_name=None, index=None):
        if parent:
            element = parent.find(tag, class_=class_name) if class_name else parent.find(tag)
            if index:
                element = parent.find_all(tag, class_=class_name)[index] if class_name else parent.find_all(tag)[index]
            if element:
                return element.get_text(strip=True)
        return "N/A"
    
    def get_review_data(self, review, type) -> dict:
        data = {}
        if type and type.lower() == "profile":
            u_c_t = review.find("div", class_="InfoContainer ng-star-inserted")
            data["username"] = self.safe_get_text(u_c_t, "p", "text-small", 1)[1:]
            data["name"] = self.safe_get_text(u_c_t, "p", "text-small", 0)
            data["country"] = self.safe_get_text(u_c_t, "p", "text-small", 3)
            data["time_text"] = self.safe_get_text(u_c_t, "span")
            
            project_price = review.find("p")
            data["project"] = self.safe_get_text(project_price, "a")
            data["price_tag"] = self.safe_get_text(project_price, "span", index=1)
            data["review_description"] = self.safe_get_text(review, "p", index=1)
            return data
        else:
            u_c_t = review.find("div", class_="InfoContainer ng-star-inserted")
            data["username"] = self.safe_get_text(u_c_t, "p", "text-small", 1)[1:]
            data["name"] = self.safe_get_text(u_c_t, "p", "text-small", 0)
            data["country"] = self.safe_get_text(u_c_t, "p", "text-small", 3)
            data["time_text"] = self.safe_get_text(u_c_t, "span")
            
            project_price = review.find("p", class_="font-medium text-small")
            data["project"] = self.safe_get_text(project_price, "a")
            data["price_tag"] = self.safe_get_text(project_price, "span", index=1)
            data["review_description"] = self.safe_get_text(review, "p", index=1)
            return data
        
    def get_generate_email(self, username: str):
        email = f"{username}@gmail.com"
        email_validation = EmailGenerate(email)
        status, msg, code = email_validation.full_email_check()
        print(msg)
        if status:
            return email
        else:
            if (code in (550, 350)):
                InvalidUsernameEmail.objects.create(username=username, status_code=code)
            return None
    
    def has_email(self, data):
        return "email" in data and bool(data["email"])
    
    def post(self, request, *args, **kwargs):
        category_slug = request.POST.get("category")
        subcategory_slug = request.POST.get("subcategory")
        category = Category.objects.get(slug=category_slug) if category_slug else None
        subcategory = SubCategory.objects.get(slug=subcategory_slug) if subcategory_slug else None
        
        urltype = request.POST.get("urltype")
        username = request.POST.get("username")
        url = request.POST.get("url")
        total_reviews = request.POST.get("total_reviews")
        html_code = base64.b64decode(request.POST.get("html_code")).decode("utf-8")
        
        # Scrapping html code-----
        all_reviews, total_reviews_count = self.scrapping_all_reviews(html_code, urltype)
                
        # check username and gig is already scrapping or not----
        existing, updated = self.username_and_url_check(username, url, total_reviews, total_reviews_count)
        if existing:
            message = "This Project/Profile already Scrapping!"
            messages.warning(request, message)
            referer = request.META.get("HTTP_REFERER", "/")
            return redirect(referer)
        
        if updated is False:
            FreelancerCompleteProfileDetails.objects.create(
                username = username,
                details_type = urltype,
                url = url,
                total_reviews = total_reviews,
                total_scrapping = total_reviews_count,
            )

        for i, review in enumerate(all_reviews, start=1):
            data = self.get_review_data(review, urltype)
            print(f"---------- Start For Review #{i}: {data["username"]}----------")
                        
            # CSV/Data Frame------------------------------------------------------
            if FreelancerReviewListWithEmail.objects.filter(username=data["username"]).exists():
                get_review_object = FreelancerReviewListWithEmail.objects.get(username=data["username"])
                get_review_object.count += 1
                get_review_object.save()
                message = "❌ username already Exist!"
                print(message)
                self.duplicated_count += 1
            elif InvalidUsernameEmail.objects.filter(username=data["username"]).exists():
                message = "❌ username already checking & invalid!"
                self.not_found_count += 1
                print(message)
            elif FiverrReviewListWithEmail.objects.filter(username=data["username"]).exists():
                message = "❌ username already Exist in Fiverr List!"
                self.duplicated_count += 1
                print(message)
            else:
                try:
                    # Email Generate & Check Email Valid or Not-----------------------
                    time.sleep(1)
                    
                    generate_email = self.get_generate_email(data["username"])
                    if generate_email is None:
                        message = "❌ Get not Email by This username!"
                        print(message)
                        self.not_found_count += 1 
                    else:
                        data["email"] = generate_email
                        # Data Save-----------------------------------------------------------
                        if self.has_email(data):
                            try:
                                object = FreelancerReviewListWithEmail.objects.create(
                                    username = data["username"],
                                    email = data["email"],
                                    country = data["country"],
                                    price_tag = data["price_tag"],
                                    time_text = data["time_text"],
                                    count = 0,
                                    category = category,
                                    sub_category = subcategory,
                                    review_description = data["review_description"]
                                )
                                self.success_count += 1
                            except Exception as e:
                                message = f"Get issues add new row!: {str(e)}"
                                print(message)
                                self.failed_count += 1
                        else:
                            self.not_found_count += 1 
                    
                    # Wait for 1 Second
                    time.sleep(1)
                except Exception as e:
                    print(f"Get Something Wrong Try/Except: {str(e)}")
            
            print(f"---------- End For Review #{i}: {data["username"]}----------")
            print("=============================================================")
        
        url = reverse("freelancerr_result")
        return redirect(f"{url}?success={self.success_count}&not_found={self.not_found_count}&dup={self.duplicated_count}&fail={self.failed_count}")

@login_required
def freelancer_result(request):
    context = {
        "success_count": request.GET.get("success", 0),
        "not_found_count": request.GET.get("not_found", 0),
        "duplicated_count": request.GET.get("dup", 0),
        "failed_count": request.GET.get("fail", 0),
    }
    return render(request, "freelancerr/result.html", context)

@login_required
def verify_freelancer_url(request):
    context = {}
    if request.method == 'POST':
        urltype = request.POST.get("urltype")
        username = request.POST.get("username")
        url = request.POST.get("url")
        if FreelancerCompleteProfileDetails.objects.filter(username=username, url=url, details_type=urltype).exists():
            data = FreelancerCompleteProfileDetails.objects.get(username=username, url=url, details_type=urltype)
        else:
            data = None
        context["data"] = data
        return render(request, "freelancerr/verify_fiverr.html", context)
    else:
        return render(request, "freelancerr/verify_fiverr.html", context)
