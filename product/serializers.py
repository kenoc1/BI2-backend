from rest_framework import serializers

from .models import ProductSubcategory, Product, ProductFamily


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "name",
            "get_absolute_url",
            "description",
            "price",
            "get_thumbnail",
            "get_image"
        )


class ProductSubcategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = ProductSubcategory
        fields = (
            "product_subcategory_id",
            "description",
            "get_absolute_url",
            "get_products",
        )


class ProductFamilySerializer(serializers.ModelSerializer):
    # products = ProductSerializer(many=True)
    # print(products)

    class Meta:
        model = ProductFamily
        fields = (
            "product_family_id",
            "description",
            "get_absolute_url",
        )
