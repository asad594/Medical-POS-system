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
]
