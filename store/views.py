from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CheckoutForm, DemoRequestForm, MedicineForm, PurchaseStockForm, SupplierForm
from .models import Medicine, Purchase, PurchaseItem, Sale, SaleItem, Supplier


def _money(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError):
        return Decimal('0.00')


def _cart(request):
    return request.session.setdefault('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_lines(cart):
    lines = []
    subtotal = Decimal('0.00')
    if not cart:
        return lines, subtotal

    medicines = Medicine.objects.filter(id__in=cart.keys()).select_related('supplier')
    medicine_map = {str(medicine.id): medicine for medicine in medicines}

    for medicine_id, quantity in cart.items():
        medicine = medicine_map.get(str(medicine_id))
        if not medicine:
            continue
        line_total = medicine.sale_price * quantity
        subtotal += line_total
        lines.append(
            {
                'medicine': medicine,
                'quantity': quantity,
                'line_total': line_total,
                'available': medicine.is_available_for_sale and quantity <= medicine.stock_quantity,
            }
        )
    return lines, subtotal


def home(request):
    form = DemoRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Request received. We will contact your medical store shortly.')
        return redirect('home')

    return render(request, 'store/home.html', {'form': form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = start_of_day + timedelta(days=1)
    today_sales = Sale.objects.filter(created_at__gte=start_of_day, created_at__lt=end_of_day)
    today_revenue = SaleItem.objects.filter(sale__in=today_sales).aggregate(total=Sum('line_total'))['total'] or Decimal('0.00')
    low_stock = Medicine.objects.filter(stock_quantity__lte=models_reorder_level()).order_by('stock_quantity')[:8]
    expiring = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30),
        stock_quantity__gt=0,
        is_active=True,
    ).order_by('expiry_date')[:8]

    context = {
        'total_medicines': Medicine.objects.filter(is_active=True).count(),
        'today_invoices': today_sales.count(),
        'today_revenue': today_revenue,
        'low_stock_count': Medicine.objects.filter(stock_quantity__lte=models_reorder_level()).count(),
        'expiry_count': Medicine.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
            stock_quantity__gt=0,
            is_active=True,
        ).count(),
        'low_stock': low_stock,
        'expiring': expiring,
        'recent_sales': Sale.objects.prefetch_related('items')[:6],
    }
    return render(request, 'store/dashboard.html', context)


def models_reorder_level():
    from django.db.models import F

    return F('reorder_level')


@login_required
def pos(request):
    cart = _cart(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        medicine_id = request.POST.get('medicine_id')

        if action == 'add':
            medicine = get_object_or_404(Medicine, pk=medicine_id, is_active=True)
            quantity = max(int(request.POST.get('quantity') or 1), 1)
            current_qty = cart.get(str(medicine.id), 0)

            if medicine.is_expired:
                messages.error(request, f'{medicine.name} is expired and cannot be sold.')
            elif medicine.stock_quantity <= 0:
                messages.error(request, f'{medicine.name} is out of stock.')
            elif current_qty + quantity > medicine.stock_quantity:
                messages.error(request, f'Only {medicine.stock_quantity} units of {medicine.name} are available.')
            else:
                cart[str(medicine.id)] = current_qty + quantity
                _save_cart(request, cart)
                messages.success(request, f'{medicine.name} added to bill.')
            next_query = request.POST.get('next_query', '').strip()
            if next_query:
                return redirect(f'{request.path}?q={next_query}')
            return redirect('pos')

        if action == 'update':
            medicine = get_object_or_404(Medicine, pk=medicine_id)
            quantity = max(int(request.POST.get('quantity') or 0), 0)
            if quantity == 0:
                cart.pop(str(medicine.id), None)
            elif quantity > medicine.stock_quantity:
                messages.error(request, f'Only {medicine.stock_quantity} units of {medicine.name} are available.')
            else:
                cart[str(medicine.id)] = quantity
            _save_cart(request, cart)
            return redirect('pos')

        if action == 'remove':
            cart.pop(str(medicine_id), None)
            _save_cart(request, cart)
            return redirect('pos')

        if action == 'clear':
            _save_cart(request, {})
            messages.info(request, 'Current bill cleared.')
            return redirect('pos')

        if action == 'checkout':
            return _checkout_sale(request, cart)

    query = request.GET.get('q', '').strip()
    medicines = Medicine.objects.filter(is_active=True).select_related('supplier')
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(barcode__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(manufacturer__icontains=query)
        )
    medicines = medicines.order_by('name', 'expiry_date')[:40]

    lines, subtotal = _cart_lines(cart)
    context = {
        'query': query,
        'medicines': medicines,
        'cart_lines': lines,
        'subtotal': subtotal,
        'checkout_form': CheckoutForm(),
    }
    return render(request, 'store/pos.html', context)


def _checkout_sale(request, cart):
    lines, subtotal = _cart_lines(cart)
    if not lines:
        messages.error(request, 'Add at least one medicine before completing the sale.')
        return redirect('pos')

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please check payment details and try again.')
        return redirect('pos')

    discount = _money(form.cleaned_data.get('discount'))
    amount_paid = _money(form.cleaned_data.get('amount_paid'))

    with transaction.atomic():
        locked_medicines = Medicine.objects.select_for_update().filter(id__in=[line['medicine'].id for line in lines])
        medicine_map = {medicine.id: medicine for medicine in locked_medicines}

        for line in lines:
            medicine = medicine_map[line['medicine'].id]
            if medicine.is_expired:
                messages.error(request, f'{medicine.name} is expired. Remove it from the bill.')
                return redirect('pos')
            if line['quantity'] > medicine.stock_quantity:
                messages.error(request, f'{medicine.name} only has {medicine.stock_quantity} units available.')
                return redirect('pos')

        sale = Sale.objects.create(
            customer_name=form.cleaned_data.get('customer_name', ''),
            customer_phone=form.cleaned_data.get('customer_phone', ''),
            payment_method=form.cleaned_data['payment_method'],
            discount=discount,
            amount_paid=amount_paid,
            created_by=request.user,
        )

        for line in lines:
            medicine = medicine_map[line['medicine'].id]
            SaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                medicine_name=medicine.name,
                batch_number=medicine.batch_number,
                quantity=line['quantity'],
                unit_price=medicine.sale_price,
                line_total=medicine.sale_price * line['quantity'],
            )
            medicine.stock_quantity -= line['quantity']
            medicine.save(update_fields=['stock_quantity', 'updated_at'])

    _save_cart(request, {})
    messages.success(request, f'Sale complete. Invoice {sale.invoice_number} created.')
    return redirect('receipt', sale_id=sale.id)


@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items'), pk=sale_id)
    return render(request, 'store/receipt.html', {'sale': sale})


@login_required
def medicines(request):
    query = request.GET.get('q', '').strip()
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medicine saved.')
        return redirect('medicines')

    medicine_list = Medicine.objects.select_related('supplier')
    if query:
        medicine_list = medicine_list.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(barcode__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(manufacturer__icontains=query)
        )

    return render(
        request,
        'store/medicines.html',
        {
            'form': form,
            'medicines': medicine_list[:100],
            'query': query,
        },
    )


@login_required
def medicine_edit(request, medicine_id):
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medicine updated.')
        return redirect('medicines')
    return render(request, 'store/medicine_edit.html', {'form': form, 'medicine': medicine})


@login_required
def suppliers(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Supplier saved.')
        return redirect('suppliers')

    return render(
        request,
        'store/suppliers.html',
        {
            'form': form,
            'suppliers': Supplier.objects.all(),
        },
    )


@login_required
def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Supplier updated.')
        return redirect('suppliers')
    return render(request, 'store/supplier_edit.html', {'form': form, 'supplier': supplier})


@login_required
def purchases(request):
    form = PurchaseStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            medicine = Medicine.objects.select_for_update().get(pk=form.cleaned_data['medicine'].pk)
            purchase = Purchase.objects.create(
                supplier=form.cleaned_data.get('supplier'),
                reference_number=form.cleaned_data.get('reference_number', ''),
                notes=form.cleaned_data.get('notes', ''),
                created_by=request.user,
            )
            PurchaseItem.objects.create(
                purchase=purchase,
                medicine=medicine,
                quantity=form.cleaned_data['quantity'],
                unit_cost=form.cleaned_data['unit_cost'],
                line_total=form.cleaned_data['unit_cost'] * form.cleaned_data['quantity'],
            )
            medicine.stock_quantity += form.cleaned_data['quantity']
            medicine.purchase_price = form.cleaned_data['unit_cost']
            if purchase.supplier:
                medicine.supplier = purchase.supplier
            medicine.save(update_fields=['stock_quantity', 'purchase_price', 'supplier', 'updated_at'])

        messages.success(request, f'Stock added for {medicine.name}.')
        return redirect('purchases')

    return render(
        request,
        'store/purchases.html',
        {
            'form': form,
            'purchases': Purchase.objects.select_related('supplier').prefetch_related('items')[:30],
        },
    )


@login_required
def reports(request):
    today = timezone.localdate()
    start = request.GET.get('start') or today.replace(day=1).isoformat()
    end = request.GET.get('end') or today.isoformat()

    sales = Sale.objects.filter(created_at__date__gte=start, created_at__date__lte=end).prefetch_related('items')
    revenue = SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('line_total'))['total'] or Decimal('0.00')
    discount = sales.aggregate(total=Sum('discount'))['total'] or Decimal('0.00')
    net_revenue = max(revenue - discount, Decimal('0.00'))
    items_sold = SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'start': start,
        'end': end,
        'sales': sales[:80],
        'revenue': revenue,
        'discount': discount,
        'net_revenue': net_revenue,
        'items_sold': items_sold,
        'invoice_count': sales.count(),
    }
    return render(request, 'store/reports.html', context)


@login_required
def alerts(request):
    today = timezone.localdate()
    low_stock = Medicine.objects.filter(stock_quantity__lte=models_reorder_level(), is_active=True).order_by('stock_quantity')
    expired = Medicine.objects.filter(expiry_date__lt=today, stock_quantity__gt=0, is_active=True).order_by('expiry_date')
    expiring = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30),
        stock_quantity__gt=0,
        is_active=True,
    ).order_by('expiry_date')
    return render(request, 'store/alerts.html', {'low_stock': low_stock, 'expired': expired, 'expiring': expiring})
