from django.shortcuts import render

from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CustomerSerializer, CustomerAddressSerializer, AddressSerializer


# @api_view(['POST'])
def login(request):
    json_string = {
        'customer': {
            "salutation": "Herr",
            "firstname": "Sven",
            "lastname": "Meiners",
            "email": "sven.meiners@gmail.com",
            "birth_date": "04.06.1998",
        },
        "address": {
            "country": "",
            "postcode": "",
            "place": "",
            "street": "",
            "house_number": "",
            "federal_state": "",
        }
    }

    serializer_address = AddressSerializer(data=json_string['customer'])
    serializer_customer = CustomerSerializer(data=json_string['address'])
    print(serializer_address)
    print(serializer_customer)
