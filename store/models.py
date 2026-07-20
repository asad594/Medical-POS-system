import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=160)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Medicine(models.Model):
    TABLET = 'tablet'
    CAPSULE = 'capsule'
    SYRUP = 'syrup'
    INJECTION = 'injection'
    CREAM = 'cream'
    DROPS = 'drops'
    OTHER = 'other'

    CATEGORY_CHOICES = [
        (TABLET, 'Tablet'),
        (CAPSULE, 'Capsule'),
        (SYRUP, 'Syrup'),
        (INJECTION, 'Injection'),
        (CREAM, 'Cream/Ointment'),
        (DROPS, 'Drops'),
        (OTHER, 'Other'),
    ]

    name = models.CharField(max_length=180)
    generic_name = models.CharField(max_length=180, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=TABLET)
    barcode = models.CharField(max_length=80, unique=True, null=True, blank=True)
    manufacturer = models.CharField(max_length=140, blank=True)
    batch_number = models.CharField(max_length=80, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'expiry_date']

    def __str__(self):
        if self.batch_number:
            return f'{self.name} - {self.batch_number}'
        return self.name

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())

    @property
    def expires_soon(self):
        if not self.expiry_date:
            return False
        return timezone.localdate() <= self.expiry_date <= timezone.localdate() + timedelta(days=30)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    @property
    def is_available_for_sale(self):
        return self.is_active and self.stock_quantity > 0 and not self.is_expired

    @property
    def stock_label(self):
        if self.is_expired:
            return 'Expired'
        if self.stock_quantity == 0:
            return 'Out of stock'
        if self.is_low_stock:
            return 'Low stock'
        return 'Available'


class Sale(models.Model):
    CASH = 'cash'
    CARD = 'card'
    EASYPAISA = 'easypaisa'
    JAZZCASH = 'jazzcash'
    CREDIT = 'credit'

    PAYMENT_CHOICES = [
        (CASH, 'Cash'),
        (CARD, 'Card'),
        (EASYPAISA, 'Easypaisa'),
        (JAZZCASH, 'JazzCash'),
        (CREDIT, 'Credit'),
    ]

    invoice_number = models.CharField(max_length=32, unique=True, blank=True)
    customer_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=40, blank=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default=CASH)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.localdate().strftime('%Y%m%d')
            self.invoice_number = f'INV-{today}-{uuid.uuid4().hex[:6].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number

    @property
    def subtotal(self):
        if not self.pk:
            return Decimal('0.00')
        return self.items.aggregate(total=models.Sum('line_total'))['total'] or Decimal('0.00')

    @property
    def payable_total(self):
        total = self.subtotal - self.discount
        return max(total, Decimal('0.00'))

    @property
    def change_due(self):
        if self.payment_method != self.CASH:
            return Decimal('0.00')
        return max(self.amount_paid - self.payable_total, Decimal('0.00'))


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    medicine_name = models.CharField(max_length=180)
    batch_number = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        if not self.medicine_name and self.medicine_id:
            self.medicine_name = self.medicine.name
        if not self.batch_number and self.medicine_id:
            self.batch_number = self.medicine.batch_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.medicine_name} x {self.quantity}'


class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    reference_number = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.reference_number or f'Purchase #{self.pk}'

    @property
    def total_amount(self):
        if not self.pk:
            return Decimal('0.00')
        return self.items.aggregate(total=models.Sum('line_total'))['total'] or Decimal('0.00')


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.line_total = self.unit_cost * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.medicine} x {self.quantity}'


class DemoRequest(models.Model):
    store_name = models.CharField(max_length=160)
    owner_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    area = models.CharField(max_length=120, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.store_name} - {self.phone}'
