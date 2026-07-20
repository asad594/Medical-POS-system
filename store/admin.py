from django.contrib import admin

from .models import DailyClosingReport, DailySession, DemoRequest, Medicine, Purchase, PurchaseItem, Sale, SaleItem, Supplier


@admin.register(DailySession)
class DailySessionAdmin(admin.ModelAdmin):
    list_display = ('business_date', 'opened_at', 'closed_at', 'opened_by', 'status')
    list_filter = ('status', 'business_date')
    search_fields = ('business_date', 'opened_by__username')


@admin.register(DailyClosingReport)
class DailyClosingReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'business_date', 'total_revenue', 'total_transactions', 'closing_time', 'generated_by')
    list_filter = ('business_date', 'generated_by')
    search_fields = ('report_number', 'business_date', 'generated_by__username')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'contact_person', 'balance')
    search_fields = ('name', 'phone', 'contact_person')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'batch_number', 'stock_quantity', 'sale_price', 'expiry_date', 'stock_label')
    list_filter = ('category', 'is_active', 'supplier')
    search_fields = ('name', 'generic_name', 'barcode', 'batch_number', 'manufacturer')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'created_at', 'payment_method', 'customer_phone', 'subtotal', 'discount', 'payable_total')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('invoice_number', 'customer_name', 'customer_phone')
    inlines = [SaleItemInline]


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'reference_number', 'created_at', 'total_amount')
    list_filter = ('created_at', 'supplier')
    search_fields = ('reference_number', 'supplier__name')
    inlines = [PurchaseItemInline]


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'owner_name', 'phone', 'area', 'created_at')
    search_fields = ('store_name', 'owner_name', 'phone', 'area')
