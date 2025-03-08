# loans/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

LOAN_CATEGORY_CHOICES = (
    ('house', 'House Loan'),
    ('car', 'Car Loan'),
)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('provider', 'Loan Provider'),
        ('customer', 'Loan Customer'),
        ('bank', 'Bank Personnel'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class LoanProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total funds provided")

    def __str__(self):
        return f"Provider: {self.user.username} - Budget: {self.total_budget}"

class FundApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    provider = models.ForeignKey(LoanProvider, on_delete=models.CASCADE, related_name='fund_applications')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fund Application by {self.provider.user.username}: {self.amount} ({self.status})"

class LoanCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')

    def __str__(self):
        return f"Customer: {self.user.username}"

class Loan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    )
    customer = models.ForeignKey('LoanCustomer', on_delete=models.CASCADE, related_name='loans')
    category = models.CharField(max_length=20, choices=LOAN_CATEGORY_CHOICES,default='house')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term = models.PositiveIntegerField(help_text="Loan term in months")
    interest_rate = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.status == 'approved':
            approved_funds = FundApplication.objects.filter(status='approved').aggregate(
                total=Sum('amount')
            )['total'] or 0
            approved_loans = Loan.objects.filter(status='approved').aggregate(
                total=Sum('amount')
            )['total'] or 0
            if approved_loans + self.amount > approved_funds:
                raise ValidationError("Total approved loans cannot exceed total approved funds from providers.")
        policy = LoanPolicy.objects.filter(active=True, category=self.category).order_by('-created_at').first()
        if not policy:
            raise ValidationError(f"No active loan policy found for {self.get_category_display()}. Please contact bank personnel.")

        if self.amount < policy.min_amount or self.amount > policy.max_amount:
            raise ValidationError(f"For {self.get_category_display()}, loan amount must be between {policy.min_amount} and {policy.max_amount}.")

        if self.interest_rate != policy.interest_rate:
            raise ValidationError(f"For {self.get_category_display()}, interest rate must be {policy.interest_rate} as per policy.")
   
        if self.term != policy.duration:
            raise ValidationError(f"For {self.get_category_display()}, loan term must be {policy.duration} months as per policy.")

    def __str__(self):
        return (f"Loan for {self.customer.user.username} ({self.get_category_display()}): "
                f"{self.amount} @ {self.interest_rate}% for {self.term} months")

class LoanPayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} on {self.payment_date}"

class LoanPolicy(models.Model):
    bank_personnel = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'bank'},
        related_name='loan_policies'  
    )
    category = models.CharField(max_length=20, choices=LOAN_CATEGORY_CHOICES, default='house')
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=4, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Loan duration in months")
    active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} Policy set by {self.bank_personnel.username} (Active: {self.active})"
