import csv
from django.core.management.base import BaseCommand
from freelancerr.models import FreelancerReviewListWithEmail
from core.models import Category, SubCategory

class Command(BaseCommand):
    help = "Import CompleteProfileDetails from CSV file"
    
    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
    
    def handle(self, *args, **kwargs):
        category = Category.objects.all().first()
        sub_category = SubCategory.objects.all().first()
        csv_file = kwargs["csv_file"]
        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print("Total Exports:", len(rows))
            
            for i, row in enumerate(rows, start=1):
                print(f"{i} - {row["email"]}")
                
                obj, created = FreelancerReviewListWithEmail.objects.get_or_create(
                    username=row["username"],
                    email=row["email"],
                    country=row["country"],
                    
                    defaults={
                        "price_tag": (row.get("price_tag", "$100-$200") or "$100-$200").strip(),
                        "time_text": (row.get("time_text", "N/A") or "N/A").strip(),
                        "count": int(row.get("count") or 0),
                        "category": category,
                        "sub_category": sub_category,
                        "review_description": (row.get("review_description") or "").strip()
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created: {obj}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Skipped (exists): {obj}"))

