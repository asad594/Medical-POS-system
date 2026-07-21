from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pos/', views.pos, name='pos'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('medicines/', views.medicines, name='medicines'),
    path('medicines/<int:medicine_id>/edit/', views.medicine_edit, name='medicine_edit'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/<int:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('purchases/', views.purchases, name='purchases'),
    path('reports/', views.reports, name='reports'),
    path('alerts/', views.alerts, name='alerts'),
    path('pos/today-transactions/', views.today_transactions, name='today_transactions'),
    path('pos/close-day/', views.close_day, name='close_day'),
    path('daily-closing/<int:report_id>/', views.daily_report_detail, name='daily_report_detail'),
    path('daily-closing/<int:report_id>/reopen/', views.reopen_day, name='reopen_day'),
    path('cashiers/', views.cashiers, name='cashiers'),
    path('cashiers/add/', views.cashier_add, name='cashier_add'),
    path('cashiers/<int:user_id>/edit/', views.cashier_edit, name='cashier_edit'),
    path('cashiers/<int:user_id>/toggle/', views.cashier_toggle, name='cashier_toggle'),
]

