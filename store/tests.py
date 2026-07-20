from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Medicine, Sale


class PosWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='staff', password='strong-test-password')
        self.client.login(username='staff', password='strong-test-password')
        self.medicine = Medicine.objects.create(
            name='Test Tablet',
            generic_name='Test Generic',
            expiry_date=timezone.localdate().replace(year=timezone.localdate().year + 1),
            sale_price=10,
            purchase_price=5,
            stock_quantity=5,
            reorder_level=2,
            barcode='T001',
        )

    def test_cannot_add_more_than_available_stock(self):
        response = self.client.post(
            reverse('pos'),
            {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 6},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('cart'), {})

    def test_checkout_creates_invoice_and_reduces_stock(self):
        self.client.post(
            reverse('pos'),
            {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 3},
        )
        response = self.client.post(
            reverse('pos'),
            {
                'action': 'checkout',
                'customer_name': 'Walk In',
                'customer_phone': '',
                'payment_method': 'cash',
                'discount': '0',
                'amount_paid': '100',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Sale.objects.count(), 1)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 2)
        self.assertEqual(self.client.session.get('cart'), {})
