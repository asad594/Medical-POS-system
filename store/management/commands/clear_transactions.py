from django.core.management.base import BaseCommand
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from store.models import Supplier, DailySession, DailyClosingReport, Sale, SaleItem, Purchase, PurchaseItem, DemoRequest


class Command(BaseCommand):
    help = 'Freshen database: Delete all transactional data, sessions, and suppliers, leaving only Medicine items.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting database freshening process...'))

        # Delete SaleItems first due to foreign keys
        count, _ = SaleItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} SaleItem records.'))

        # Delete Sales
        count, _ = Sale.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} Sale records.'))

        # Delete PurchaseItems
        count, _ = PurchaseItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} PurchaseItem records.'))

        # Delete Purchases
        count, _ = Purchase.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} Purchase records.'))

        # Delete DailyClosingReports
        count, _ = DailyClosingReport.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} DailyClosingReport records.'))

        # Delete DailySessions
        count, _ = DailySession.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} DailySession records.'))

        # Delete DemoRequests
        count, _ = DemoRequest.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} DemoRequest records.'))

        # Delete Suppliers
        count, _ = Supplier.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} Supplier records.'))

        # Clear active sessions
        count, _ = Session.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Cleared {count} active login sessions.'))

        # Clear admin logs
        count, _ = LogEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} Django admin log entries.'))

        self.stdout.write(self.style.SUCCESS('Database freshened successfully! Only Medicine items and User accounts remain.'))
