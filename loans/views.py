from django.shortcuts import render

# Create your views here.
# loans/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import FundApplication, Loan, LoanPayment, LoanPolicy, LoanCustomer, LoanProvider
from .serializers import (
    FundApplicationSerializer, 
    LoanSerializer, 
    LoanPaymentSerializer, 
    LoanPolicySerializer
)

# Loan Provider ViewSet: view status of loan fund applications
class FundApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FundApplication.objects.all()
    serializer_class = FundApplicationSerializer
    def get_queryset(self):
        user = self.request.user    
        if user.role == 'provider':
            provider = get_object_or_404(LoanProvider, user=user)
            return self.queryset.filter(provider=provider)
        elif user.role == 'bank':   
            return self.queryset.all()
        return self.queryset.none()

# Loan Customer ViewSet: view status of loan applications and make payments
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    def get_queryset(self):
        user = self.request.user        
        if user.role == 'customer':
            customer = get_object_or_404(LoanCustomer, user=user)
            qs = self.queryset.filter(customer=customer)        
        elif user.role == 'bank':
            qs = self.queryset.all()
        else:
            qs = self.queryset.none()   
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

# ViewSet for Loan Payments
class LoanPaymentViewSet(viewsets.ModelViewSet):
    queryset = LoanPayment.objects.all()
    serializer_class = LoanPaymentSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.validated_data['loan']
        
        if request.user.role in ['customer', 'bank']:
            try:
                customer = LoanCustomer.objects.get(user=request.user)
            except LoanCustomer.DoesNotExist:
                return Response({"detail": "No loan customer profile found for payment."}, status=status.HTTP_403_FORBIDDEN)
            if loan.customer != customer:
                return Response(
                    {"detail": "You do not have permission to make a payment for this loan."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"detail": "You do not have permission to make a payment for this loan."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Bank Personnel ViewSet: view and manage both fund and loan applications and policies
class LoanPolicyViewSet(viewsets.ModelViewSet):
    queryset = LoanPolicy.objects.all()
    serializer_class = LoanPolicySerializer
    def get_queryset(self):
        user = self.request.user        
        if user.role == 'bank':
            return self.queryset.filter(bank_personnel=user)
        return self.queryset.none()
