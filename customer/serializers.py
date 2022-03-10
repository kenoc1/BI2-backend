from rest_framework import serializers

from .models import Customer, CustomerAddress, Address
from product.serializers import ProductSerializer


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = (
            "customer_id",
            "salutation",
            "firstname",
            "lastname",
            "email",
            "birth_date"
        )

    def create(self, validated_data):
        customer = Customer.objects.create(**validated_data)
        return customer


class CustomerAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerAddress
        fields = (
            "salutation",
            "firstname",
            "lastname",
            "email",
            "address",
            "birth_date"
        )


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = (
            "country",
            "postcode",
            "place",
            "street",
            "house_number",
            "federal_state"
        )
