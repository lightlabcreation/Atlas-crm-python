from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Finance Dashboard
    path('', views.accountant_dashboard, name='dashboard'),
    
    # Accountant Dashboard
    path('accountant/', views.accountant_dashboard, name='accountant_dashboard'),
    
    # Payment Management
    path('payments/', views.payment_management, name='payments'),
    path('payment-management/', views.payment_management, name='payment_management'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/<int:payment_id>/edit/', views.edit_payment, name='payment_edit'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='payment_delete'),
    path('payments/export/', views.export_payments, name='export_payments'),
    
    # Truvo Payments
    path('truvo-payments/create/', views.truvo_payment_create, name='truvo_payment_create'),
    path('truvo-payments/<int:payment_id>/edit/', views.edit_truvo_payment, name='edit_truvo_payment'),
    path('truvo-payments/<int:payment_id>/delete/', views.delete_truvo_payment, name='delete_truvo_payment'),
    
    # Order Management
    path('orders/', views.order_management, name='orders'),
    path('order-management/', views.order_management, name='order_management'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/invoice/', views.invoice_generation, name='invoice_generation'),
    
    # Fee Management
    path('fees/', views.fees_general, name='fees'),
    path('fees/order/<int:order_id>/', views.fee_management, name='fee_management'),
    path('fees/management/', views.fees_general, name='fee_management_general'),
    
    # Invoice Management
    path('invoices/', views.invoice_list, name='invoices'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.edit_invoice, name='edit_invoice'),
    path('invoices/<int:invoice_id>/delete/', views.delete_invoice, name='delete_invoice'),
    
    # Reports
    path('reports/', views.financial_reports, name='reports'),
    path('reports/financial/', views.financial_reports, name='financial_reports'),
    path('reports/sales/', views.sales_reports, name='sales_reports'),
    path('reports/payments/', views.payment_reports, name='payment_reports'),
    
    # Bank Reconciliation
    path('bank-reconciliation/', views.bank_reconciliation, name='bank_reconciliation'),
    
    # Payment Platforms
    path('payment-platforms/', views.payment_platforms, name='payment_platforms'),
    path('payment-platforms/add/', views.add_payment_platform, name='add_payment_platform'),
    path('payment-platforms/<int:platform_id>/edit/', views.edit_payment_platform, name='edit_payment_platform'),
    path('payment-platforms/<int:platform_id>/delete/', views.delete_payment_platform, name='delete_payment_platform'),
    path('payment-platforms/<int:platform_id>/test/', views.test_platform_connection, name='test_platform_connection'),
    path('payment-platforms/<int:platform_id>/sync/', views.sync_platform_data, name='sync_platform_data'),
    path('payment-platforms/<int:platform_id>/logs/', views.platform_sync_logs, name='platform_sync_logs'),
]