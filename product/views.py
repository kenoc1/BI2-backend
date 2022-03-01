import json
import re
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404

from django.db import connections
from itertools import combinations

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from util.page_object import Page_object
from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:56]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class PersonalRecommendationsList(APIView):
    def get(self, request, format=None):
        product_skus = []
        customer_id = 5769  # TODO: get id from logged user
        with connections['oracle_db'].cursor() as c:
            sql = f"SELECT PRODUKT_SKU, MATCH FROM EMPF_PERSONENBEZOGEN " \
                  f"WHERE KUNDE_ID = {customer_id} ORDER BY MATCH DESC"
            c.execute(sql)
            for row in c:
                product_skus.append(row[0])
        products = get_products_by_skus(product_skus)
        if len(products) < 20:
            products = add_discounts(products)
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
        associations = get_association(product.sku)
        if len(associations) < 10:
            associations = add_discounts(associations)

        serializer_product = ProductSerializer(product)
        serializer_associations = ProductSerializer(associations, many=True)

        return Response({'product': serializer_product.data, 'associations': serializer_associations.data})


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


class CartRecommendationsList(APIView):
    def post(self, request):
        products = request.data.get('items')
        products = list(set(products))
        skus = []
        if len(products) == 2:
            skus = get_associations_two_products(products)
        else:
            skus = get_associations_more_products(products)
        for sku in products:
            one_product_associations = get_associations_from_db(sku)
            for association_sku in one_product_associations:
                skus.append(association_sku)
        associations = get_products_by_skus(list(set(skus)))
        associations = add_discounts(associations)
        serializer = ProductSerializer(associations, many=True)
        return Response(serializer.data)


def get_associations_two_products(products):
    associations_two_products = []
    with connections['oracle_db'].cursor() as c:
        sql = f"SELECT ITEMS_ADD FROM ASSOBESTELLUNG " \
              f"WHERE ITEMS_BASE LIKE '%{products[0]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[1]}%' " \
              f"ORDER BY LIFT DESC"
        c.execute(sql)
        for row in c:
            associations_two_products.append(re.search(r'\d+', row[0]).group())
    return associations_two_products


def get_associations_three_products(products):
    associations_three_products = []
    with connections['oracle_db'].cursor() as c:
        sql = f"SELECT ITEMS_ADD FROM ASSOBESTELLUNG " \
              f"WHERE ITEMS_BASE LIKE '%{products[0]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[1]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[2]}%' " \
              f"ORDER BY LIFT DESC"
        c.execute(sql)
        for row in c:
            associations_three_products.append(re.search(r'\d+', row[0]).group())
    return associations_three_products


def get_associations_more_products(products):
    product_skus_of_associations = []
    combinations_two_products = [",".join(map(str, comb)) for comb in combinations(products, 2)]
    for combination in combinations_two_products:
        two_products = combination.split(",")
        associations_two_products = get_associations_two_products(two_products)
        for association in associations_two_products:
            product_skus_of_associations.append(association)
    combinations_three_products = [",".join(map(str, comb)) for comb in combinations(products, 3)]
    for combination in combinations_three_products:
        three_products = combination.split(",")
        associations_three_products = get_associations_three_products(three_products)
        for association in associations_three_products:
            product_skus_of_associations.append(association)
    product_skus_of_associations = list(set(product_skus_of_associations))
    return product_skus_of_associations


@api_view(['POST'])
def search(request):
    page_index = request.data.get('pg', 1)
    query = request.data.get('query', '')

    if query:
        products = Product.objects.filter(
            (Q(name__icontains=query) | Q(description__icontains=query)) & Q(origin=1))

        serializer = ProductSerializer(products, many=True)
        p = Paginator(serializer.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__)})
    else:
        return Response({"page": []})


def get_product_by_sku(req_sku):
    product = Product.objects.filter(Q(sku=req_sku) & Q(origin=1))[:1].get()
    return product


def get_products_by_skus(skus):
    products = []
    for sku in skus:
        products.append(get_product_by_sku(sku))
    return products


def get_association(sku):
    products = []
    if sku:
        products = get_products_by_skus(get_associations_from_db(sku))
    return products


def add_discounts(associations):
    products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:10]
    for product in products:
        associations.append(product)
    return associations[:10]


def get_associations_from_db(sku):
    associations = []
    with connections['oracle_db'].cursor() as c:
        sql = "SELECT ITEMS_ADD FROM ASSOBESTELLUNG WHERE ITEMS_BASE = '{" + str(
            sku) + "}' ORDER BY CONFIDENCE DESC FETCH FIRST 10 ROWS ONLY"
        c.execute(sql)
        for row in c:
            associations.append(re.search(r'\d+', row[0]).group())
    return associations
