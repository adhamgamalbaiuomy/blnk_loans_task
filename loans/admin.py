from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.core.exceptions import PermissionDenied
from .models import User, LoanProvider, FundApplication, LoanCustomer, Loan, LoanPayment, LoanPolicy

class UserAdmin(DefaultUserAdmin):
    fieldsets = DefaultUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = DefaultUserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'category', 'amount', 'status', 'created_at')
admin.site.register(Loan, LoanAdmin)


class LoanPaymentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if request.user.role in ['customer', 'bank']:
            try:
                customer = obj.loan.customer
                if customer.user != request.user:
                    raise PermissionDenied("You do not have permission to make a payment for this loan.")
            except Exception as e:
                raise PermissionDenied("Payment not allowed.")
        super().save_model(request, obj, form, change)

admin.site.register(LoanPayment, LoanPaymentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(LoanProvider)
admin.site.register(FundApplication)
admin.site.register(LoanCustomer)
admin.site.register(LoanPolicy)
