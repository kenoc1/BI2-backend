from django.shortcuts import render

from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CustomerSerializer, CustomerAddressSerializer, AddressSerializer
from .models import Customer, CustomerAddress, Address
from order.models import Cart
from django.contrib.auth.models import User, UserManager


@api_view(['POST'])
def login(request):
    data = request.data
    django_user = User.objects.create_user(data.get('login_data').get('username'), data.get('customer').get('email'),
                                           data.get('login_data').get('password'))
    data['customer'].update({'django_user': django_user.id})
    customer = Customer.objects.create(**data['customer'])
    address = Address.objects.create(**data['address'])
    customer_address = CustomerAddress.objects.create(**{
        "address": address,
        "customer": customer,
        "address_type": "Rechnungsadresse"
    })
    cart = Cart.objects.create(**{
        "customer": customer,
        "total_price": 0.0,
        "total_quantity": 0.0
    })
    if customer_address:
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)
