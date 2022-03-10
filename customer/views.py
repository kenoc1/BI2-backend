from django.db import connections
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
def register(request):
    data = request.data
    with connections['default'].cursor() as c:
        sql = f"SELECT TOP 1 products.id FROM products " \
              f"WHERE products.id = { data.get('login_data').get('username')}"
        c.execute(sql)
        for row in c:
            return Response({'information': 'invalid_user'})
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


class UserInformation(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        customer = Customer.objects.filter(django_user__in=User.objects.filter(username=user)).first()
        address = Address.objects.filter(customeraddress__customer=customer).first()
        print(address)
        serializer_user = CustomerSerializer(customer)
        serializer_address = AddressSerializer(address)
        print(serializer_user.data)
        print(serializer_address.data)
        return Response({'user_data': serializer_user.data, 'address_data': serializer_address.data})