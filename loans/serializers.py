# loans/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import FundApplication, Loan, LoanPayment, LoanPolicy


class FundApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundApplication
        fields = '__all__'


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'
    
    def update(self, instance, validated_data):
    
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        try:
           
            instance.full_clean()
        except ValidationError as e:
            
            if "Total approved loans cannot exceed" in str(e):
                instance.status = "rejected"
            else:
                
                raise serializers.ValidationError(e)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        if instance.status == "rejected":
            rep["message"] = "Loan auto rejected: total available funds cannot cover this loan."
        return rep

class LoanPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanPayment
        fields = '__all__'


class LoanPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanPolicy
        fields = '__all__'
