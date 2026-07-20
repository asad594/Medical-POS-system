from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DailyClosingReport, DailySession, Medicine, Sale


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


class DailyClosingSystemTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='admin-password')
        self.client.login(username='admin', password='admin-password')
        self.medicine = Medicine.objects.create(
            name='Test Tablet',
            sale_price=10,
            purchase_price=5,
            stock_quantity=100,
        )

    def test_pos_sale_associates_with_active_session(self):
        self.client.post(reverse('pos'), {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 2})
        self.client.post(
            reverse('pos'),
            {
                'action': 'checkout',
                'customer_name': 'Ali',
                'customer_phone': '03001234567',
                'payment_method': 'cash',
                'discount': '0',
                'amount_paid': '20',
            },
        )
        session = DailySession.objects.filter(status='open').first()
        self.assertIsNotNone(session)
        self.assertEqual(session.sales.count(), 1)

        response = self.client.get(reverse('today_transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ali')

    def test_close_day_creates_report_and_archives_transactions(self):
        self.client.post(reverse('pos'), {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 5})
        self.client.post(
            reverse('pos'),
            {
                'action': 'checkout',
                'customer_name': 'Saad',
                'customer_phone': '03007654321',
                'payment_method': 'cash',
                'discount': '2',
                'amount_paid': '50',
            },
        )

        session = DailySession.objects.filter(status='open').first()
        self.assertIsNotNone(session)

        response = self.client.post(reverse('close_day'), follow=True)
        self.assertEqual(response.status_code, 200)

        session.refresh_from_db()
        self.assertEqual(session.status, 'closed')

        report = DailyClosingReport.objects.filter(session=session).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.total_revenue, 48)
        self.assertEqual(report.total_transactions, 1)
        self.assertEqual(report.total_quantity_sold, 5)

        response = self.client.get(reverse('today_transactions'))
        self.assertNotContains(response, 'Saad')

        self.client.post(reverse('pos'), {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 1})
        self.client.post(
            reverse('pos'),
            {
                'action': 'checkout',
                'customer_name': 'Zain',
                'customer_phone': '',
                'payment_method': 'cash',
                'discount': '0',
                'amount_paid': '10',
            },
        )
        new_session = DailySession.objects.filter(status='open').first()
        self.assertIsNotNone(new_session)
        self.assertNotEqual(new_session.id, session.id)

    def test_cannot_reopen_day_with_accounting_lock(self):
        self.client.post(reverse('pos'), {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 1})
        self.client.post(reverse('pos'), {'action': 'checkout', 'payment_method': 'cash', 'discount': '0', 'amount_paid': '10'})
        self.client.post(reverse('close_day'))

        session1 = DailySession.objects.all().order_by('id')[0]
        report1 = session1.report

        self.client.post(reverse('pos'), {'action': 'add', 'medicine_id': self.medicine.id, 'quantity': 1})
        self.client.post(reverse('pos'), {'action': 'checkout', 'payment_method': 'cash', 'discount': '0', 'amount_paid': '10'})
        self.client.post(reverse('close_day'))

        response = self.client.post(reverse('reopen_day', args=[report1.id]), follow=True)
        self.assertContains(response, 'Accounting lock')

        session1.refresh_from_db()
        self.assertEqual(session1.status, 'closed')
