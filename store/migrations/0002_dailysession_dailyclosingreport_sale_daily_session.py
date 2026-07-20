import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def create_historical_sessions(apps, schema_editor):
    DailySession = apps.get_model('store', 'DailySession')
    DailyClosingReport = apps.get_model('store', 'DailyClosingReport')
    Sale = apps.get_model('store', 'Sale')
    User = apps.get_model('auth', 'User')

    default_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not default_user:
        return

    sales_without_session = Sale.objects.filter(daily_session__isnull=True).order_by('created_at')
    if not sales_without_session.exists():
        return

    from collections import defaultdict
    sales_by_date = defaultdict(list)
    for sale in sales_without_session:
        sale_date = sale.created_at.date()
        sales_by_date[sale_date].append(sale)

    for sale_date, day_sales in sales_by_date.items():
        session, created = DailySession.objects.get_or_create(
            business_date=sale_date,
            defaults={
                'opened_at': day_sales[0].created_at,
                'closed_at': day_sales[-1].created_at,
                'opened_by': default_user,
                'closed_by': default_user,
                'status': 'closed',
            }
        )

        for sale in day_sales:
            sale.daily_session = session
            sale.save(update_fields=['daily_session'])

        total_revenue = 0
        total_discount = 0
        total_quantity_sold = 0
        cash_sales_total = 0
        card_sales_total = 0
        easypaisa_sales_total = 0
        jazzcash_sales_total = 0
        credit_sales_total = 0

        SaleItem = apps.get_model('store', 'SaleItem')

        for sale in day_sales:
            items = SaleItem.objects.filter(sale=sale)
            subtotal = sum(item.line_total for item in items)
            discount = sale.discount
            payable_total = max(subtotal - discount, 0)

            total_revenue += payable_total
            total_discount += discount
            total_quantity_sold += sum(item.quantity for item in items)

            if sale.payment_method == 'cash':
                cash_sales_total += payable_total
            elif sale.payment_method == 'card':
                card_sales_total += payable_total
            elif sale.payment_method == 'easypaisa':
                easypaisa_sales_total += payable_total
            elif sale.payment_method == 'jazzcash':
                jazzcash_sales_total += payable_total
            elif sale.payment_method == 'credit':
                credit_sales_total += payable_total

        total_transactions = len(day_sales)
        average_sale = total_revenue / total_transactions if total_transactions > 0 else 0

        DailyClosingReport.objects.get_or_create(
            session=session,
            defaults={
                'report_number': f"EOD-{sale_date.strftime('%Y%m%d')}-{session.id}",
                'business_date': sale_date,
                'opening_time': session.opened_at,
                'closing_time': session.closed_at,
                'total_revenue': total_revenue,
                'total_transactions': total_transactions,
                'total_quantity_sold': total_quantity_sold,
                'total_discount': total_discount,
                'total_tax': 0,
                'net_revenue': total_revenue,
                'average_sale': average_sale,
                'first_transaction_time': day_sales[0].created_at,
                'last_transaction_time': day_sales[-1].created_at,
                'cash_sales_total': cash_sales_total,
                'card_sales_total': card_sales_total,
                'easypaisa_sales_total': easypaisa_sales_total,
                'jazzcash_sales_total': jazzcash_sales_total,
                'credit_sales_total': credit_sales_total,
                'generated_by': default_user,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_date', models.DateField(unique=True)),
                ('opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('closed', 'Closed')], default='open', max_length=10)),
                ('closed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='closed_sessions', to=settings.AUTH_USER_MODEL)),
                ('opened_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='opened_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-business_date'],
            },
        ),
        migrations.CreateModel(
            name='DailyClosingReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_number', models.CharField(max_length=32, unique=True)),
                ('business_date', models.DateField(unique=True)),
                ('opening_time', models.DateTimeField()),
                ('closing_time', models.DateTimeField()),
                ('total_revenue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_transactions', models.PositiveIntegerField()),
                ('total_quantity_sold', models.PositiveIntegerField()),
                ('total_discount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('net_revenue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('average_sale', models.DecimalField(decimal_places=2, max_digits=12)),
                ('first_transaction_time', models.DateTimeField(blank=True, null=True)),
                ('last_transaction_time', models.DateTimeField(blank=True, null=True)),
                ('cash_sales_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('card_sales_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('easypaisa_sales_total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('jazzcash_sales_total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('credit_sales_total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='CLOSED', max_length=10)),
                ('generated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='generated_reports', to=settings.AUTH_USER_MODEL)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='report', to='store.dailysession')),
            ],
            options={
                'ordering': ['-business_date'],
            },
        ),
        migrations.AddField(
            model_name='sale',
            name='daily_session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sales', to='store.dailysession'),
        ),
        migrations.RunPython(create_historical_sessions),
    ]
