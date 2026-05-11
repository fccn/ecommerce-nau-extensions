from django.urls import path
from .views import PendingPaymentsView

urlpatterns = [
    path('pending-payments/', PendingPaymentsView.as_view(), name='pending_payments'),
]
