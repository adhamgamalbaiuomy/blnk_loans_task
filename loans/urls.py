# loans/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FundApplicationViewSet, LoanViewSet, LoanPaymentViewSet, LoanPolicyViewSet

router = DefaultRouter()
router.register(r'fund-applications', FundApplicationViewSet, basename='fundapplication')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'payments', LoanPaymentViewSet, basename='loanpayment')
router.register(r'policies', LoanPolicyViewSet, basename='loanpolicy')

urlpatterns = [
    path('api/', include(router.urls)),
]
