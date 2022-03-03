import stripe
import cx_Oracle
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render
from django.db import connections
from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from customer.models import Customer
from .models import Order, OrderItem, Cart
from .serializers import OrderSerializer, MyOrderSerializer, MyOrderItemSerializer


@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    print(request.data)
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        stripe.api_key = settings.STRIPE_SECRET_KEY
        paid_amount = sum(item.get('quantity') * item.get('product').price for item in serializer.validated_data['items'])

        try:
            charge = stripe.Charge.create(
                amount=int(paid_amount * 100),
                currency='USD',
                description='Charge from Djackets',
                source=serializer.validated_data['stripe_token']
            )

            serializer.save(user=request.user, paid_amount=paid_amount)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrdersList(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        print(request.user)
        cart = Cart.objects.filter(customer__django_user__in=User.objects.filter(username=request.user))
        cart_id = cart.values("cart_id")[0]['cart_id']
        print(cart_id)
        try:
            results = []
            with connections['default'].cursor() as c:
                sql = f"SELECT BESTELLUNG.BESTELLUNG_ID, WARENKORB_ID, CAST(MENGE AS Numeric(12, 2)), LISTENVERKAUFSPREIS, PROUKT_NAME, PRODUKT.PRODUKT_ID " \
                      f"FROM BI21.BESTELLUNG, BI21.BESTELLPOSITION, BI21.PRODUKT " \
                      f"WHERE BESTELLUNG.BESTELLUNG_ID=BESTELLPOSITION.BESTELLUNG_ID AND " \
                      f"BESTELLPOSITION.PRODUKT_ID=PRODUKT.PRODUKT_ID AND " \
                      f"WARENKORB_ID = {cart_id}"
                c.execute(sql)
                last_number = -1
                product_arr = []
                for row in c:
                    print(row)
                    if row[0] == last_number or last_number == -1:
                        product_arr.append({'name': row[4], 'quantity': row[2], 'price': row[3], 'product_id': row[5]})
                    else:
                        results.append({'order_id': last_number, 'products': product_arr})
                        product_arr = [{'name': row[4], 'quantity': row[2], 'price': row[3], 'product_id': row[5]}]
                    last_number = row[0]
                results.append({'order_id': last_number, 'products': product_arr})
                return Response(results)
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)
