from rest_framework import serializers

from .models import ProductSubcategory, Product, ProductFamily, ProductCategory, ProductDivision


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "name",
            "get_absolute_url",
            "description",
            "get_price",
            "get_image",
            "get_thumbnail",
            "sku",
            "recycle",
            "lowfat",
            "discount",
            "origin",
            "evaluation"
        )


class ProductSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSubcategory
        fields = (
            "product_subcategory_id",
            "description",
            "get_absolute_url",
        )


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = (
            "product_category_id",
            "description",
            "get_absolute_url",
        )


class ProductDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDivision
        fields = (
            "product_division_id",
            "description",
            "get_absolute_url",
        )


class ProductFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFamily
        fields = (
            "product_family_id",
            "description",
            "get_absolute_url",
        )
