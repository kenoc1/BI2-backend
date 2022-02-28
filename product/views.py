import json
import re
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404

from django.db import connections

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from util.page_object import Page_object
from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:56]
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
        associations = get_association(product.sku)
        if len(associations) < 10:
            associations = add_discounts(associations)

        serializer_product = ProductSerializer(product)
        print(serializer_product.data)

        serializer_associations = ProductSerializer(associations, many=True)
        print(serializer_associations.data)

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


def get_order_count_day():
    with connections['oracle_db'].cursor() as c:
        sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between sysdate - 1 AND sysdate;"
        c.execute(sql)
        if c:
            return c[0]
        else:
            return 0


def get_order_count_month():
    with connections['oracle_db'].cursor() as c:
        sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between add_months(trunc(sysdate, 'mm'), -1) and last_day(add_months(trunc(sysdate, 'mm'), -1));"
        c.execute(sql)
        if c:
            return c[0]
        else:
            return 0


def get_order_count():
    with connections['oracle_db'].cursor() as c:
        sql = "select COUNT(BESTELLUNG_ID) FROM BESTELLPOSITION;"
        c.execute(sql)
        if c:
            return c[0]
        else:
            return 0


def get_orders(days):
    orders = []
    with connections['oracle_db'].cursor() as c:
        sql = "select TRUNC(RECHNUNGSDATUM), count(RECHNUNG_ID) as ANZAHL_KAEUFE from RECHNUNG where RECHNUNGSDATUM between sysdate - '{" + str(
            days) + "}' AND sysdate group by TRUNC(RECHNUNGSDATUM)"
        c.execute(sql)
        for row in c:
            orders.append(row[0])
            # orders.append(re.search(r'\d+', row[0]).group())
    return orders


def get_revenue(days):
    revenue = []
    with connections['oracle_db'].cursor() as c:
        sql = "select TRUNC(RECHNUNGSDATUM), sum(SUMME_BRUTTO) as ANZAHL_KAEUFE from RECHNUNG where RECHNUNGSDATUM between sysdate - '{" + str(
            days) + "}' AND sysdate group by TRUNC(RECHNUNGSDATUM)"
        c.execute(sql)
        for row in c:
            revenue.append(row[0])
            # revenue.append(re.search(r'\d+', row[0]).group())
    return revenue


def get_top_seller():
    products = []
    with connections['oracle_db'].cursor() as c:
        sql = "SELECT BESTELLPOSITION.PRODUKT_ID, COUNT(BESTELLPOSITION.PRODUKT_ID) FROM BESTELLPOSITION, BESTELLUNG WHERE BESTELLPOSITION.BESTELLUNG_ID = BESTELLUNG.BESTELLUNG_ID group by BESTELLPOSITION.PRODUKT_ID;"
        c.execute(sql)
        for row in c:
            products.append(row[0])
            # products.append(re.search(r'\d+', row[0]).group())
    return products
