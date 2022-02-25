import json

import cx_Oracle
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from util.page_object import Page_object
from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer, ProductCategorySerializer, ProductDivisionSerializer
from django.db import connections

import getFavoriteProduct


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:10]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


def get_page_index(request):
    if request.GET.get('pg') is None:
        return 1
    else:
        return request.GET.get('pg')


class ProductDetail(APIView):
    def get(self, request, product_slug, format=None):
        products = Product.objects.filter(slug=product_slug).exclude(image__isnull=True)[0]
        serializer = ProductSerializer(products)
        return Response(serializer.data)


class Categories(APIView):
    def get(self, request, format=None):
        families = []
        for family in ProductFamily.objects.all():
            divisions = []
            for division in ProductDivision.objects.filter(product_family=family):
                categories = []
                for category in ProductCategory.objects.filter(product_division=division):
                    subcategories = []
                    for subcategory in ProductSubcategory.objects.filter(product_category=category):
                        subcategories.append({'description': subcategory.description, 'slug': subcategory.get_absolute_url()})
                    categories.append({'description': category.description, 'slug': category.get_absolute_url(), 'subcategories': subcategories})
                divisions.append({'description': division.description, 'slug': division.get_absolute_url(), 'categories': categories})
            families.append({'description': family.description, 'slug': family.get_absolute_url(), 'divisions': divisions})
        return Response(families)


class FamilyDetail(APIView):
    def get_object(self, family_slug):
        try:
            return ProductFamily.objects.get(slug=family_slug)
        except ProductFamily.DoesNotExist:
            raise Http404

    def get(self, request, family_slug):
        page_index = get_page_index(request)
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


class DivisionDetail(APIView):
    def get_object(self, division_slug):
        try:
            return ProductDivision.objects.get(slug=division_slug)
        except ProductDivision.DoesNotExist:
            raise Http404

    def get(self, request, family_slug, division_slug):
        print(family_slug)
        print(division_slug)
        page_index = get_page_index(request)
        division = self.get_object(division_slug)
        products = Product.objects.filter(subcategory__product_category__product_division__in=division).exclude(
            image__isnull=True).exclude(image="Kein Bild")
        serializer_family = ProductDivisionSerializer(division)
        serializer_products = ProductSerializer(products, many=True)
        p = Paginator(serializer_products.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__), 'family_data': serializer_family.data})


class CategoryDetail(APIView):
    def get_object(self, category_slug):
        try:
            return ProductCategory.objects.get(slug=category_slug)
        except ProductCategory.DoesNotExist:
            raise Http404

    def get(self, request, category_slug):
        page_index = get_page_index(request)
        category = self.get_object(category_slug)
        products = Product.objects.filter(subcategory__product_category__in=category).exclude(
            image__isnull=True).exclude(image="Kein Bild")
        serializer_family = ProductCategorySerializer(category)
        serializer_products = ProductSerializer(products, many=True)
        p = Paginator(serializer_products.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__), 'family_data': serializer_family.data})


class SubcategoryDetail(APIView):
    def get_object(self, subcategory_slug):
        try:
            return ProductSubcategory.objects.get(slug=subcategory_slug)
        except ProductSubcategory.DoesNotExist:
            raise Http404

    def get(self, request, subcategory_slug):
        page_index = get_page_index(request)
        subcategory = self.get_object(subcategory_slug)
        products = Product.objects.filter(subcategory__in=subcategory).exclude(
            image__isnull=True).exclude(image="Kein Bild")
        serializer_family = ProductSubcategorySerializer(subcategory)
        serializer_products = ProductSerializer(products, many=True)
        p = Paginator(serializer_products.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__), 'family_data': serializer_family.data})

class favoritProduct(APIView):

    def get_product_SKU(self):
        try:
            productSKU = []
            with connections['default'].cursor() as cursor:
                cursor.execute("""select distinct P.SKU, count(P.SKU) as anzahl
                                    from BESTELLUNG
                                             join BESTELLPOSITION B on BESTELLUNG.BESTELLUNG_ID = B.BESTELLUNG_ID
                                             join PRODUKT P on P.PRODUKT_ID = B.PRODUKT_ID
                                             join PRODUKT_SUBKATEGORIE PS on P.PRODUKTKLASSE_ID = PS.PRODUKT_SUBKATEGORIE_ID
                                             join PRODUKT_KATEGORIE PK on PS.PRODUKT_KATEGORIE_ID = PK.PRODUKT_KATEGORIE_ID
                                             join PRODUKT_SPARTE S on PK.PRODUKT_SPARTE_ID = S.PRODUKT_SPARTE_ID
                                             join PRODUKT_FAMILIE PF on S.PRODUKT_FAMILIE_ID = PF.PRODUKT_FAMILIE_ID
                                    where PF.PRODUKT_FAMILIE_ID = 6
                                    group by P.SKU
                                    order by Anzahl desc;""")
                for row in cursor:
                    productSKU.append(row[0])
            return productSKU[:10]
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get (self, request):
        productSKU= self.get_product_SKU()
        product= get_products_by_skus(productSKU)
        serializer= ProductSerializer(product, many=True)
        return Response(serializer.data)

def get_product_by_sku(req_sku):
    product = Product.objects.filter(Q(sku=req_sku) & Q(origin=1))[:1].get()
    return product


def get_products_by_skus(skus):
    products = []
    for sku in skus:
        products.append(get_product_by_sku(sku))

    return products

@api_view(['POST'])
def search(request):
    page_index = request.data.get('pg', 1)
    query = request.data.get('query', '')

    if query:
        products = Product.objects.filter(
            (Q(name__icontains=query) | Q(description__icontains=query)) & Q(origin=1)).exclude(
            image__isnull=True).exclude(image="Kein Bild")[0:20]

        print(Product.objects)
        serializer = ProductSerializer(products, many=True)
        p = Paginator(serializer.data, 20)
        current_page = p.page(page_index)
        page_object = Page_object(current_page, p.num_pages)
        return Response({'page': json.dumps(page_object.__dict__)})
    else:
        return Response({"page": []})
