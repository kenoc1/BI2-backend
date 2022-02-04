from django.db.models import Q
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True)[0:4]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class OneProduct(APIView):
    def get(self, request, format=None):
        product = Product.objects.first()
        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ProductDetail(APIView):
    def get(self, request, product_slug, format=None):
        products = Product.objects.filter(slug=product_slug).exclude(image__isnull=True)[0]
        serializer = ProductSerializer(products)
        return Response(serializer.data)


class FamilyDetail(APIView):
    def get_object(self, family_slug):
        try:
            return ProductFamily.objects.get(slug=family_slug)
        except ProductFamily.DoesNotExist:
            raise Http404

    def get(self, request, family_slug, format=None):
        family = self.get_object(family_slug)
        divisions = ProductDivision.objects.filter(product_family=family)
        products = Product.objects.filter(subcategory__product_category__product_division__in=divisions).exclude(
            image__isnull=True).exclude(image="Kein Bild")[0:50]
        serializer_products = ProductSerializer(products, many=True)
        serializer_family = ProductFamilySerializer(family)
        print(serializer_family)
        print(serializer_products)

        return Response({'products': serializer_products.data, 'family_data': serializer_family.data})


@api_view(['POST'])
def search(request):
    query = request.data.get('query', '')

    if query:
        products = Product.objects.filter(
            (Q(name__icontains=query) | Q(description__icontains=query)) & Q(origin=1)).exclude(
            image__isnull=True).exclude(image="Kein Bild")[0:20]

        serializer = ProductSerializer(products, many=True)
        print(serializer.data)
        return Response(serializer.data)
    else:
        return Response({"products": []})
