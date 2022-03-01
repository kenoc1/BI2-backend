from django.contrib import admin

from .models import Order, OrderItem, CartProduct, Cart

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CartProduct)
admin.site.register(Cart)
