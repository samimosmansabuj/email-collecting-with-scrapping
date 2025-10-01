from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views import View
from bs4 import BeautifulSoup
import time
from .utils import EmailGenerate
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET

@login_required
def fiverr_data(request):
    data_list = ReviewListWithEmail.objects.all().order_by("-updated_at")
    return render(request, "fiverr/data_list.html", {
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
class ScrapFiverrDataView(View):
    template_name = "fiverr/scrapping_form.html"
    success_count = 0
    not_found_count = 0
    duplicated_count = 0
    failed_count = 0

    def get(self, request, *args, **kwargs):
        context = {}
        context["caregory"] = Category.objects.all()
        return render(request, self.template_name, context)
    
    def username_and_url_check(self, username, url, total_reviews, total_reviews_count):
        if CompleteGigDetails.objects.filter(username = username, url = url).exists():
            get_object = CompleteGigDetails.objects.get(username = username, url = url)
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
            all_reviews = soup.find_all("span", class_="freelancer-review-item-wrapper")
        else:
            all_reviews = soup.find_all("li", class_="review-item-component")
        total_reviews_count = len(all_reviews)
        print("Total reviews found:", total_reviews_count)
        return all_reviews, total_reviews_count
    
    def safe_get_text(self, parent, tag, class_name=None):
        if parent:
            element = parent.find(tag, class_=class_name) if class_name else parent.find(tag)
            if element:
                return element.get_text(strip=True)
        return "N/A"
    
    def get_review_data(self, review, type=None) -> dict:
        data = {}
        if type and type.lower() == "profile":
            data["username"] = self.safe_get_text(review, "p", "l6pj4a1eb")
            data["repeated"] = self.safe_get_text(review.find("div", class_="l6pj4a11o"), "p")
            data["country"] = self.safe_get_text(review.find("div", class_="country"), "p")
            data["time_text"] = self.safe_get_text(review, "time")
            data["review_description"] = self.safe_get_text(review.find("div", class_="reliable-review-description review-description"), "p")
            price_tag = review.find("p", string=lambda text: text and "$" in text) or review.find("p", string=lambda text: text and "US$" in text)
            data["price_tag"] = price_tag.get_text(strip=True) if price_tag else "N/A"
        else:
            data["username"] = self.safe_get_text(review, "p", "_66nk381cr")
            data["repeated"] = self.safe_get_text(review.find("div", class_="_66nk38109"), "p")
            data["country"] = self.safe_get_text(review.find("div", class_="country"), "p")
            data["time_text"] = self.safe_get_text(review, "time")
            data["review_description"] = self.safe_get_text(review.find("div", class_="reliable-review-description review-description"), "p")
            price_tag = review.find("p", string=lambda text: text and "$" in text) or review.find("p", string=lambda text: text and "US$" in text)
            data["price_tag"] = price_tag.get_text(strip=True) if price_tag else "N/A"
        return data

    def get_generate_email(self, username: str):
        email = f"{username}@gmail.com"
        email_validation = EmailGenerate(email)
        status, msg, code = email_validation.full_email_check()
        print(msg)
        if status:
            return email
        else:
            if (code in (550,)):
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
        html_code = request.POST.get("html_code")
        
        # Scrapping html code-----
        all_reviews, total_reviews_count = self.scrapping_all_reviews(html_code, urltype)
        
        # check username and gig is already scrapping or not----
        existing, updated = self.username_and_url_check(username, url, total_reviews, total_reviews_count)
        if existing:
            message = "This Gig/Profile already Scrapping!"
            messages.warning(request, message)
            referer = request.META.get("HTTP_REFERER", "/")
            return redirect(referer)
        
        if updated is False:
            CompleteGigDetails.objects.create(
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
            if ReviewListWithEmail.objects.filter(username=data["username"]).exists():
                get_review_object = ReviewListWithEmail.objects.get(username=data["username"])
                get_review_object.count += 1
                get_review_object.save()
                message = "❌ username already Exist!"
                print(message)
                self.duplicated_count += 1
            elif InvalidUsernameEmail.objects.filter(username=data["username"]).exists():
                message = "❌ username already checking & invalid!"
                self.not_found_count += 1
                print(message)
            else:
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
                            object = ReviewListWithEmail.objects.create(
                                username = data["username"],
                                email = data["email"],
                                repeated = True if data["repeated"] else False,
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
            
            print(f"---------- End For Review #{i}: {data["username"]}----------")
            print("=============================================================")
        
        url = reverse("result")
        return redirect(f"{url}?success={self.success_count}&not_found={self.not_found_count}&dup={self.duplicated_count}&fail={self.failed_count}")

@login_required
def result(request):
    context = {
        "success_count": request.GET.get("success", 0),
        "not_found_count": request.GET.get("not_found", 0),
        "duplicated_count": request.GET.get("dup", 0),
        "failed_count": request.GET.get("fail", 0),
    }
    return render(request, "fiverr/result.html", context)

@login_required
def verify_fiverr_url(request):
    context = {}
    if request.method == 'POST':
        urltype = request.POST.get("urltype")
        username = request.POST.get("username")
        url = request.POST.get("url")
        if CompleteGigDetails.objects.filter(username=username, url=url, details_type=urltype).exists():
            data = CompleteGigDetails.objects.get(username=username, url=url, details_type=urltype)
        else:
            data = None
        context["data"] = data
        return render(request, "fiverr/verify_fiverr.html", context)
    else:
        return render(request, "fiverr/verify_fiverr.html", context)
