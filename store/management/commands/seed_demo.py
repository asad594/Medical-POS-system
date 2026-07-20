from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.crypto import get_random_string

from store.models import Medicine, Supplier


class Command(BaseCommand):
    help = 'Create local preview admin, suppliers, and medicines.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--skip-admin', action='store_true')

    def handle(self, *args, **options):
        if not options['skip_admin']:
            username = options['username']
            password = get_random_string(16)
            User = get_user_model()
            admin, _ = User.objects.get_or_create(username=username)
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password(password)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Local preview login: {username} / {password}'))

        supplier_a, _ = Supplier.objects.get_or_create(
            name='Karachi Pharma Distributor',
            defaults={
                'contact_person': 'Sales Desk',
                'phone': '021-111-222-333',
                'address': 'Medicine Market, Saddar, Karachi',
            },
        )
        supplier_b, _ = Supplier.objects.get_or_create(
            name='Sindh Medical Supplies',
            defaults={
                'contact_person': 'Accounts',
                'phone': '021-444-555-666',
                'address': 'Shahrah-e-Faisal, Karachi',
            },
        )

        today = timezone.localdate()
        samples = [
            {
                'name': 'Paracetamol 500mg',
                'generic_name': 'Paracetamol',
                'category': Medicine.TABLET,
                'manufacturer': 'Local Pharma',
                'batch_number': 'PCM-2401',
                'expiry_date': today + timedelta(days=180),
                'purchase_price': 2.50,
                'sale_price': 5.00,
                'stock_quantity': 450,
                'reorder_level': 60,
                'supplier': supplier_a,
                'barcode': '100001',
            },
            {
                'name': 'Amoxicillin 500mg',
                'generic_name': 'Amoxicillin',
                'category': Medicine.CAPSULE,
                'manufacturer': 'Care Labs',
                'batch_number': 'AMX-113',
                'expiry_date': today + timedelta(days=120),
                'purchase_price': 14.00,
                'sale_price': 22.00,
                'stock_quantity': 80,
                'reorder_level': 30,
                'supplier': supplier_a,
                'barcode': '100002',
            },
            {
                'name': 'Cough Syrup 120ml',
                'generic_name': 'Dextromethorphan',
                'category': Medicine.SYRUP,
                'manufacturer': 'WellCare',
                'batch_number': 'CS-778',
                'expiry_date': today + timedelta(days=28),
                'purchase_price': 130.00,
                'sale_price': 190.00,
                'stock_quantity': 24,
                'reorder_level': 12,
                'supplier': supplier_b,
                'barcode': '100003',
            },
            {
                'name': 'ORS Sachet',
                'generic_name': 'Oral Rehydration Salts',
                'category': Medicine.OTHER,
                'manufacturer': 'HealthPack',
                'batch_number': 'ORS-56',
                'expiry_date': today + timedelta(days=300),
                'purchase_price': 18.00,
                'sale_price': 30.00,
                'stock_quantity': 12,
                'reorder_level': 25,
                'supplier': supplier_b,
                'barcode': '100004',
            },
            {
                'name': 'Eye Drops 10ml',
                'generic_name': 'Lubricant eye drops',
                'category': Medicine.DROPS,
                'manufacturer': 'VisionMed',
                'batch_number': 'ED-19',
                'expiry_date': today - timedelta(days=8),
                'purchase_price': 95.00,
                'sale_price': 140.00,
                'stock_quantity': 6,
                'reorder_level': 10,
                'supplier': supplier_a,
                'barcode': '100005',
            },
        ]

        for data in samples:
            Medicine.objects.update_or_create(barcode=data['barcode'], defaults=data)

        self.stdout.write(self.style.SUCCESS('Sample suppliers and medicines are ready.'))
