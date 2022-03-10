import cx_Oracle
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render
import datetime
from django.db import connections
from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from customer.models import Customer
from product.models import Product
from .models import Order, OrderItem, Cart, Bill, PaymentMethod, PaymentMethodOrder
from .serializers import OrderSerializer, MyOrderSerializer, MyOrderItemSerializer


@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    cart = Cart.objects.filter(customer__django_user__in=User.objects.filter(username=request.user)).first()
    order = Order.objects.create(**{
        'cart': cart,
        'order_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'order_status': 'Abgeschlossen',
        'total_quantity': len(request.data['items']),
        'origin': 1
    })
    payment = PaymentMethod.objects.filter(name__icontains=request.data['payment_service']).first()
    PaymentMethodOrder.objects.create(**{
        'payment_method': payment,
        'order': order
    })
    total_net = 0
    total_gross = 0
    for item in request.data['items']:
        product = Product.objects.filter(sku=item['product']).filter(origin=1).first()
        print(item)
        # total_net = total_net + item['price'] * item['quantity']
        # total_gross = total_gross + item['quantity'] * item['price'] * (1 + product.mwst)
        total_net = total_net + float(item['price']) * float(item['quantity'])
        total_gross = total_gross + float(item['quantity']) * float(item['price']) * (1 + product.mwst)
        OrderItem.objects.create(**{
            'product': product,
            'order': order,
            'quantity': item['quantity']
        })
    bill = Bill.objects.create(**{
        'order': order,
        'billing_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_gross': total_gross,
        'total_net': total_net,
    })
    return Response(status=status.HTTP_201_CREATED)


class OrdersList(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        cart = Cart.objects.filter(customer__django_user__in=User.objects.filter(username=request.user))
        cart_id = cart.values("cart_id")[0]['cart_id']
        try:
            results = []
            with connections['default'].cursor() as c:
                sql = f"SELECT BESTELLUNG.BESTELLUNG_ID, WARENKORB_ID, CAST(MENGE AS Numeric(12, 2)), LISTENVERKAUFSPREIS, PROUKT_NAME, PRODUKT.PRODUKT_ID " \
                      f"FROM BI21.BESTELLUNG, BI21.BESTELLPOSITION, BI21.PRODUKT " \
                      f"WHERE BESTELLUNG.BESTELLUNG_ID=BESTELLPOSITION.BESTELLUNG_ID AND " \
                      f"BESTELLPOSITION.PRODUKT_ID=PRODUKT.PRODUKT_ID AND " \
                      f"WARENKORB_ID = {cart_id} ORDER BY BESTELLUNG.BESTELLUNG_ID DESC"
                c.execute(sql)
                last_number = -1
                product_arr = []
                for row in c:
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
