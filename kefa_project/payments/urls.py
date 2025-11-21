from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:tournament_id>/', views.initiate_payment, name='initiate'),
    path('proof/<int:payment_id>/', views.payment_proof_upload, name='proof_upload'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('paystack/callback/', views.paystack_webhook, name='paystack_callback'),
    path('flutterwave/webhook/', views.flutterwave_webhook, name='flutterwave_webhook'),
    path('flutterwave/callback/', views.flutterwave_callback, name='flutterwave_callback'),
    path('admin/verify/<int:payment_id>/', views.verify_offline_payment, name='verify_offline'),
    path('admin/queue/', views.payment_verification_queue, name='admin_payment_queue'),
]
