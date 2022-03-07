import json
import cx_Oracle
import re

from customer.models import Customer
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from itertools import combinations

from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from util.page_object import Page_object
from .models import Product, ProductSubcategory, ProductFamily, ProductDivision, ProductCategory
from .serializers import ProductSerializer, ProductSubcategorySerializer, ProductFamilySerializer, \
    ProductCategorySerializer, ProductDivisionSerializer
from django.db import connections


class LatestProductsList(APIView):
    def get(self, request, format=None):
        products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:56]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


def get_page_index(request):
    if request.GET.get('pg') is None:
        return 1
    else:
        return request.GET.get('pg')


class PersonalRecommendationsList(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        print(request.user)
        customer = Customer.objects.filter(django_user__in=User.objects.filter(username=request.user))[:1].get()
        if customer:
            customer_id = customer.customer_id
            product_skus = []
            with connections['default'].cursor() as c:
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
        return Response()


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
                        subcategories.append(
                            {'description': subcategory.description, 'slug': subcategory.get_absolute_url()})
                    categories.append({'description': category.description, 'slug': category.get_absolute_url(),
                                       'subcategories': subcategories})
                divisions.append({'description': division.description, 'slug': division.get_absolute_url(),
                                  'categories': categories})
            families.append(
                {'description': family.description, 'slug': family.get_absolute_url(), 'divisions': divisions})
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
        page_index = get_page_index(request)
        print(page_index)
        division = self.get_object(division_slug)
        products = Product.objects.filter(subcategory__product_category__product_division=division)
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


class FavoriteProductByFamilySlug(APIView):
    def get_product_SKU(self, family_slug):
        try:
            productSKU = []
            print(family_slug)
            with connections['default'].cursor() as cursor:
                cursor.execute(f"""select distinct P.SKU, count(P.SKU) as anzahl
                                    from BESTELLUNG
                                             join BESTELLPOSITION B on BESTELLUNG.BESTELLUNG_ID = B.BESTELLUNG_ID
                                             join PRODUKT P on P.PRODUKT_ID = B.PRODUKT_ID
                                             join PRODUKT_SUBKATEGORIE PS on P.PRODUKTKLASSE_ID = PS.PRODUKT_SUBKATEGORIE_ID
                                             join PRODUKT_KATEGORIE PK on PS.PRODUKT_KATEGORIE_ID = PK.PRODUKT_KATEGORIE_ID
                                             join PRODUKT_SPARTE S on PK.PRODUKT_SPARTE_ID = S.PRODUKT_SPARTE_ID
                                             join PRODUKT_FAMILIE PF on S.PRODUKT_FAMILIE_ID = PF.PRODUKT_FAMILIE_ID
                                    where PF.SLUG = '{family_slug}'
                                    group by P.SKU
                                    order by Anzahl desc
                                    fetch first 10 rows only;""")
                for row in cursor:
                    productSKU.append(row[0])
            return productSKU
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get(self, request, family_slug):
        productSKU = self.get_product_SKU(family_slug)
        product = get_products_by_skus(productSKU)
        serializer = ProductSerializer(product, many=True)
        return Response(serializer.data)


def get_product_by_sku(req_sku):
    product = Product.objects.filter(Q(sku=req_sku))[:1].get()
    return product


def get_products_by_skus(skus):
    products = []
    for sku in skus:
        products.append(get_product_by_sku(sku))
    return products


class FavoriteProduct(APIView):
    def get_product_SKU(self):
        try:
            productSKU = []
            with connections['default'].cursor() as cursor:
                cursor.execute(f"""select distinct P.SKU, count(P.SKU) as anzahl
                                    from BESTELLUNG
                                             join BESTELLPOSITION B on BESTELLUNG.BESTELLUNG_ID = B.BESTELLUNG_ID
                                             join PRODUKT P on P.PRODUKT_ID = B.PRODUKT_ID
                                    group by P.SKU
                                    order by Anzahl desc
                                    fetch first 10 rows only;""")
                for row in cursor:
                    productSKU.append(row[0])
            return productSKU
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get(self, request):
        productSKU = self.get_product_SKU()
        print(productSKU)
        product = get_products_by_skus(productSKU)
        serializer = ProductSerializer(product, many=True)
        return Response(serializer.data)


class CartRecommendationsList(APIView):
    def post(self, request):
        req_products = request.data.get('items')
        req_products = list(set(req_products))
        associations = []
        distinct_associations = []
        sorted_association_skus = []
        if len(req_products) == 2:
            associations = get_associations_two_products(req_products)
        else:
            associations = get_associations_more_products(req_products)
        for sku in req_products:
            one_product_associations = get_associations_from_db(sku)
            for association_sku in one_product_associations:
                associations.append(association_sku)

        # create distinct list with best lift per product
        for association in associations:
            if any(x.sku == association.sku for x in distinct_associations):
                for a in distinct_associations:
                    if a.sku == association.sku:
                        a.lift = association.lift
            else:
                distinct_associations.append(association)
        # sort by lift desc
        distinct_associations.sort(key=lambda x: x.lift, reverse=True)
        # get list with product skus
        for association in distinct_associations:
            sorted_association_skus.append(association.sku)

        res_products = get_products_by_skus(list(set(sorted_association_skus)))
        res_products = add_discounts(res_products)
        serializer = ProductSerializer(res_products, many=True)
        return Response(serializer.data)


class Association:
    def __init__(self, sku, lift):
        self.sku = sku
        self.lift = lift

    def __str__(self):
        return "{0} , {1}".format(str(self.sku), str(self.lift))


def get_associations_two_products(products):
    associations_two_products = []
    with connections['default'].cursor() as c:
        sql = f"SELECT ITEMS_ADD, LIFT FROM ASSOBESTELLUNG " \
              f"WHERE ITEMS_BASE LIKE '%{products[0]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[1]}%' " \
              f"ORDER BY LIFT DESC"
        c.execute(sql)
        for row in c:
            association = Association(re.search(r'\d+', row[0]).group(), row[1])
            associations_two_products.append(association)
    return associations_two_products


def get_associations_three_products(products):
    associations_three_products = []
    with connections['default'].cursor() as c:
        sql = f"SELECT ITEMS_ADD FROM ASSOBESTELLUNG " \
              f"WHERE ITEMS_BASE LIKE '%{products[0]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[1]}%' " \
              f"AND ITEMS_BASE LIKE '%{products[2]}%' " \
              f"ORDER BY LIFT DESC"
        c.execute(sql)
        for row in c:
            association = Association(re.search(r'\d+', row[0]).group(), row[1])
            associations_three_products.append(association)
    return associations_three_products


def get_associations_more_products(products):
    associations = []
    combinations_two_products = [",".join(map(str, comb)) for comb in combinations(products, 2)]
    for combination in combinations_two_products:
        two_products = combination.split(",")
        associations_two_products = get_associations_two_products(two_products)
        for association in associations_two_products:
            associations.append(association)
    combinations_three_products = [",".join(map(str, comb)) for comb in combinations(products, 3)]
    for combination in combinations_three_products:
        three_products = combination.split(",")
        associations_three_products = get_associations_three_products(three_products)
        for association in associations_three_products:
            associations.append(association)
    return associations


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


def get_association(sku):
    products = []
    if sku:
        skus = []
        associations = get_associations_from_db(sku)
        for association in associations:
            skus.append(association.sku)
        products = get_products_by_skus(skus)
    return products


def add_discounts(associations):
    products = Product.objects.exclude(image__isnull=True).order_by('-discount')[:10]
    for product in products:
        associations.append(product)
    return associations[:10]


def get_associations_from_db(sku):
    associations = []
    with connections['default'].cursor() as c:
        sql = "SELECT ITEMS_ADD, LIFT FROM ASSOBESTELLUNG WHERE ITEMS_BASE = '{" + str(
            sku) + "}' ORDER BY CONFIDENCE DESC FETCH FIRST 10 ROWS ONLY"
        c.execute(sql)
        for row in c:
            associations.append(Association(re.search(r'\d+', row[0]).group(), row[1]))
    return associations
