from rest_framework import serializers

from .models import ProductSubcategory, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "product_id",
            "name",
            "get_absolute_url",
            "description",
            "price",
            "get_image",
            "get_thumbnail"
        )


class SubcategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = ProductSubcategory
        fields = (
            "id",
            "name",
            "get_absolute_url",
            "products",
        )
