from rest_framework import serializers

from .models import Order, OrderItem, Bill

from product.serializers import ProductForOrderSerializer


class MyOrderItemSerializer(serializers.ModelSerializer):    
    product = ProductForOrderSerializer()

    class Meta:
        model = OrderItem
        fields = (
            "product",
            "quantity",
        )


class MyBillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bill
        fields = (
            "total_gross",
            "total_net",
        )


class MyOrderSerializer(serializers.ModelSerializer):
    items = MyOrderItemSerializer(many=True)
    # bill = MyBillSerializer()

    class Meta:
        model = Order
        fields = (
            # "bill",
            "items",
            "order_id",
            "order_date",
            "total_quantity",
        )


class OrderItemSerializer(serializers.ModelSerializer):    
    class Meta:
        model = OrderItem
        fields = (
            "price",
            "product",
            "quantity",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "address",
            "zipcode",
            "place",
            "phone",
            "stripe_token",
            "items",
        )
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
        return order