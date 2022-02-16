import json
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404

import cx_Oracle
from django.db import connections

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from util.page_object import Page_object
from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:10]
        # products = Product.objects.exclude(image__isnull=True)[0:4]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class OneProduct(APIView):
    def get(self, request, format=None):
        product = Product.objects.first()
        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ProductDetail(APIView):
    def get(self, request, product_slug, format=None):
        product = Product.objects.filter(Q(slug=product_slug) & Q(origin=1))[:1].get()
        print("now")
        print(product)
        print(product.product_id)
        assosiations = get_assosiation(product.product_id)
        print(assosiations)

        serializer_product = ProductSerializer(product)
        print(serializer_product.data)
        serializer_assosiations = ProductSerializer(assosiations, many=True)
        print(serializer_assosiations.data)


        return Response({'product': serializer_product.data, 'assosiations': serializer_assosiations.data})


class FamilyDetail(APIView):
    def get_object(self, family_slug):
        try:
            return ProductFamily.objects.get(slug=family_slug)
        except ProductFamily.DoesNotExist:
            raise Http404

    def get(self, request, family_slug):
        if request.GET.get('pg') is None:
            page_index = 1
        else:
            page_index = request.GET.get('pg')
        print(page_index)
        family = self.get_object(family_slug)
        divisions = ProductDivision.objects.filter(product_family=family)
        products = Product.objects.filter(subcategory__product_category__product_division__in=divisions).exclude(
            image__isnull=True).exclude(image="Kein Bild")
        serializer_family = ProductFamilySerializer(family)

        serializer_products = ProductSerializer(products, many=True)
        p = Paginator(serializer_products.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__), 'family_data': serializer_family.data})

@api_view(['POST'])
def search(request):
    page_index = request.data.get('pg', 1)
    query = request.data.get('query', '')

    if query:
        products = Product.objects.filter(
            (Q(name__icontains=query) | Q(description__icontains=query)) & Q(origin=1))

        print(Product.objects)
        serializer = ProductSerializer(products, many=True)
        p = Paginator(serializer.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__)})
    else:
        return Response({"page": []})


def get_product_by_id(id):
    product = Product.objects.filter(Q(product_id=id) & Q(origin=1))[:1].get()
    return product


def get_products_by_ids(product_ids):
    products = []
    for id in product_ids:
        products.append(get_product_by_id(id))

    return products

def get_assosiation(product_id):
    products = []

    if product_id:
        products = get_products_by_ids(get_assosiations_from_db(product_id))
    return products

def get_assosiations_from_db(product_id):
    assosiations = []
    with connections['oracle_db'].cursor() as c:
        c.execute(
            f"SELECT CONSEQUENT_NAME FROM DM$VRBESTELLUNG WHERE extractValue(ANTECEDENT, '/itemset/item/item_name') ='{product_id}' FETCH FIRST 10 ROWS ONLY")  # use triple quotes if you want to spread your query across multiple lines
        for row in c:
            assosiations.append(row[0])

    return assosiations



