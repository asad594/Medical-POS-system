from django import forms

from .models import DemoRequest, Medicine, Purchase, Supplier


class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = ['store_name', 'owner_name', 'phone', 'area', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'address', 'balance']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            'name',
            'generic_name',
            'category',
            'barcode',
            'manufacturer',
            'batch_number',
            'expiry_date',
            'purchase_price',
            'sale_price',
            'stock_quantity',
            'reorder_level',
            'supplier',
            'is_active',
        ]
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PurchaseStockForm(forms.Form):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False)
    reference_number = forms.CharField(max_length=80, required=False)
    medicine = forms.ModelChoiceField(queryset=Medicine.objects.filter(is_active=True))
    quantity = forms.IntegerField(min_value=1)
    unit_cost = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=120, required=False)
    customer_phone = forms.CharField(max_length=40, required=False)
    payment_method = forms.ChoiceField(choices=[])
    discount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, initial=0)
    amount_paid = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, initial=0)

    def __init__(self, *args, **kwargs):
        from .models import Sale

        super().__init__(*args, **kwargs)
        self.fields['payment_method'].choices = Sale.PAYMENT_CHOICES
