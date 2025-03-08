from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from loans.models import Loan, LoanPolicy, FundApplication, LoanCustomer, LoanProvider
from loans.serializers import LoanSerializer

User = get_user_model()

class LoanTestCase(TestCase):
    def setUp(self):
        # Create test users.
        self.provider_user = User.objects.create_user(
            username="provider1", password="testpass", role="provider", is_staff=True)
        self.customer_user = User.objects.create_user(
            username="customer1", password="testpass", role="customer", is_staff=True)
        self.bank_user = User.objects.create_user(
            username="bank1", password="testpass", role="bank", is_staff=True)

        self.provider_profile = LoanProvider.objects.create(user=self.provider_user, total_budget="100000.00")
        self.customer_profile = LoanCustomer.objects.create(user=self.customer_user)
        self.bank_customer_profile = LoanCustomer.objects.create(user=self.bank_user)
        self.fund_application = FundApplication.objects.create(
            provider=self.provider_profile, amount="100000.00", status="approved")

        # Create LoanPolicy records.
        self.house_policy = LoanPolicy.objects.create(
            bank_personnel=self.bank_user,
            category="house",
            min_amount="50000.00",
            max_amount="500000.00",
            interest_rate="4.50",
            duration=360,
            active=True,
            # created_at is auto-set.
        )
        self.car_policy = LoanPolicy.objects.create(
            bank_personnel=self.bank_user,
            category="car",
            min_amount="5000.00",
            max_amount="100000.00",
            interest_rate="7.00",
            duration=60,
            active=True,
        )
        self.valid_loan = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="50000.00",
            term=360,
            interest_rate="4.50",
            status="pending",
        )
        self.pending_loan = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="20000.00",
            term=360,
            interest_rate="4.50",
            status="pending",
        )

    def test_valid_loan_creation(self):
        """A valid loan should pass validation and be saved as approved if funds allow."""
        loan = self.valid_loan
        loan.status = "approved"
        try:
            loan.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError raised unexpectedly: {e}")
        loan.save()
        self.assertEqual(loan.status, "approved")

    def test_invalid_loan_policy_amount(self):
        """A loan with an amount below the policy's minimum should raise a validation error."""
        loan = Loan(
            customer=self.customer_profile,
            category="house",
            amount="40000.00",  
            term=360,
            interest_rate="4.50",
            status="pending"
        )
        with self.assertRaises(ValidationError) as context:
            loan.full_clean()
        self.assertIn("loan amount must be between", str(context.exception).lower())

    def test_invalid_loan_policy_interest_rate(self):
        """A loan with an incorrect interest rate should raise a validation error."""
        loan = Loan(
            customer=self.customer_profile,
            category="house",
            amount="100000.00",
            term=360,
            interest_rate="5.00",  
            status="pending"
        )
        with self.assertRaises(ValidationError) as context:
            loan.full_clean()
        self.assertIn("interest rate must be 4.50", str(context.exception))

    def test_invalid_loan_policy_term(self):
        """A loan with an incorrect term should raise a validation error."""
        loan = Loan(
            customer=self.customer_profile,
            category="car",  
            amount="20000.00",
            term=48,  
            interest_rate="7.00",
            status="pending"
        )
        with self.assertRaises(ValidationError) as context:
            loan.full_clean()
        self.assertIn("loan term must be 60", str(context.exception))

    def test_global_funds_constraint(self):
        """
        Test that approving a loan which would cause total approved loans to exceed available funds
        raises a ValidationError.
        """
        
        loan = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="250000.00",
            term=360,
            interest_rate="4.50",
            status="pending"
        )
        loan.status = "approved"
        with self.assertRaises(ValidationError) as context:
            loan.full_clean()
        self.assertIn("total approved loans cannot exceed", str(context.exception).lower())

    def test_auto_reject_logic_in_serializer(self):
        """
        Test that when updating a loan to 'approved' violates the funds constraint,
        the serializer auto-rejects the loan and returns a message.
        """
        
        loan = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="250000.00",  
            term=360,
            interest_rate="4.50",
            status="pending"
        )
        
        data = {"status": "approved"}
        serializer = LoanSerializer(instance=loan, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_loan = serializer.save()
        
        self.assertEqual(updated_loan.status, "rejected")
        rep = serializer.to_representation(updated_loan)
        self.assertIn("message", rep)
        self.assertEqual(rep["message"], "Loan auto rejected: total available funds cannot cover this loan.")

    def test_multiple_loans_approved_within_funds(self):
        """
        Test that multiple approved loans whose sum is within the available funds can be saved.
        """
        
        loan1 = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="50000.00",
            term=360,
            interest_rate="4.50",
            status="pending"
        )
        loan2 = Loan.objects.create(
            customer=self.customer_profile,
            category="house",
            amount="50000.00",
            term=360,
            interest_rate="4.50",
            status="pending"
        )
        # Approve loan1.
        loan1.status = "approved"
        loan1.full_clean()
        loan1.save()
        # Approve loan2.
        loan2.status = "approved"
        try:
            loan2.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError raised unexpectedly for valid loans: {e}")
        loan2.save()
        # Check that total approved loans do not exceed available funds.
        total_approved = Loan.objects.filter(status="approved").aggregate(total=Sum("amount"))["total"] or 0
        self.assertLessEqual(float(total_approved), 100000.00)
