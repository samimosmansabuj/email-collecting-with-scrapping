import csv
from django.core.management.base import BaseCommand
from fiverr.models import FiverrReviewListWithEmail

class Command(BaseCommand):
    help = "Import CompleteGigDetails from CSV file"
    
    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
    
    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]
        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print("Total Exports:", len(rows))
            
            for i, row in enumerate(rows, start=1):
                print(f"{i} - {row["email"]}")
                
                obj, created = FiverrReviewListWithEmail.objects.get_or_create(
                    username=row["username"],
                    email=row["email"],
                    country=row["country"],
                    
                    defaults={
                        "repeated": True if row.get("repeated", None) else False,
                        "price_tag": (row.get("price_tag", "$100-$200") or "$100-$200").strip(),
                        "proficiency": (row.get("proficiency", "medium").lower() or "medium").strip(),
                        "time_text": (row.get("time_text", "N/A") or "N/A").strip(),
                        "count": int(row.get("count") or 0),
                        "category": (row.get("category") or "").strip(),
                        "sub_category": (row.get("category") or "").strip(),
                        "review_description": (row.get("review_description") or "").strip()
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created: {obj}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Skipped (exists): {obj}"))

