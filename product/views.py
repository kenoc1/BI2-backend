import json
import cx_Oracle
import re

from customer.models import Customer
from django.contrib.auth.models import User

from datetime import date, timedelta
from operator import itemgetter
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404

from django.db import connections
from itertools import combinations
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status, authentication, permissions
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
        if request.GET.get('pg') is None:
            page_index = 1
        else:
            page_index = request.GET.get('pg')
        family = self.get_object(family_slug)
        divisions = ProductDivision.objects.filter(product_family=family)
        products = Product.objects.filter(subcategory__product_category__product_division__in=divisions).exclude(
            image__isnull=True).exclude(image="Kein Bild")

        if not request.GET.get('ftr') is None:
            filter = request.GET.get('ftr')
            products = products.filter(evaluation__in=filter)

        if not request.GET.get('pr') is None:
            priceRange = request.GET.get('pr').split(',')
            products = products.filter(price__lte=priceRange[1], price__gte=priceRange[0])

        # check order params
        if not request.GET.get('psrt') is None:
            if request.GET.get('psrt') == 'HighToLow':
                products = products.order_by('-price')
            else:
                products = products.order_by('price')
        elif not request.GET.get('nsrt') is None:
            if request.GET.get('nsrt') == 'HighToLow':
                products = products.order_by('name')
            else:
                products = products.order_by('-name')

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
        division = self.get_object(division_slug)
        products = Product.objects.filter(subcategory__product_category__product_division=division)
        if not request.GET.get('ftr') is None:
            filter = request.GET.get('ftr')
            products = products.filter(evaluation__in=filter)

        if not request.GET.get('pr') is None:
            priceRange = request.GET.get('pr').split(',')
            products = products.filter(price__lte=priceRange[1], price__gte=priceRange[0])

        if not request.GET.get('psrt') is None:
            if request.GET.get('psrt') == 'HighToLow':
                products = products.order_by('-price')
            else:
                products = products.order_by('price')
        elif not request.GET.get('nsrt') is None:
            if request.GET.get('nsrt') == 'HighToLow':
                products = products.order_by('name')
            else:
                products = products.order_by('-name')
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
    def get_product_skus(self, family_slug):
        try:
            product_skus = []
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
                    product_skus.append(row[0])
            return product_skus
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get(self, request, family_slug):
        product_skus = self.get_product_skus(family_slug)
        products = get_products_by_skus(product_skus)
        serializer = ProductSerializer(products, many=True)
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
    def get_product_skus(self):
        try:
            product_skus = []
            with connections['default'].cursor() as cursor:
                cursor.execute(f"""select distinct P.SKU, count(P.SKU) as anzahl
                                    from BESTELLUNG
                                             join BESTELLPOSITION B on BESTELLUNG.BESTELLUNG_ID = B.BESTELLUNG_ID
                                             join PRODUKT P on P.PRODUKT_ID = B.PRODUKT_ID
                                    group by P.SKU
                                    order by Anzahl desc
                                    fetch first 10 rows only;""")
                for row in cursor:
                    product_skus.append(row[0])
            return product_skus
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get(self, request):
        product_skus = self.get_product_skus()
        print(product_skus)
        products = get_products_by_skus(product_skus)
        serializer = ProductSerializer(products, many=True)
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
            sku) + "}' ORDER BY LIFT DESC FETCH FIRST 10 ROWS ONLY"
        c.execute(sql)
        for row in c:
            associations.append(Association(re.search(r'\d+', row[0]).group(), row[1]))
    return associations


def delete_duplicates(old_l):
    seen = set()
    new_l = []
    for d in old_l:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_l.append(d)
    return new_l


class AssociationsMr(APIView):
    def get(self, request, format=None):
        asso = []
        with connections['default'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEHERR, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEHERR, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'ruleid': row[0], 'itembaseproductsku': row[2],
                             'itembaseproductname': row[3],
                             'itemaddproductsku': row[5], 'itemaddproductname': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class AssociationsMs(APIView):
    def get(self, request, format=None):
        asso = []
        with connections['default'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEFRAU, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEFRAU, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'ruleid': row[0], 'itembaseproductsku': row[2],
                             'itembaseproductname': row[3],
                             'itemaddproductsku': row[5], 'itemaddproductname': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class AssociationsOrder(APIView):
    def get(self, request, format=None):
        asso = []
        with connections['default'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOBESTELLUNG, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOBESTELLUNG, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'ruleid': row[0], 'itembaseproductsku': row[2],
                             'itembaseproductname': row[3],
                             'itemaddproductsku': row[5], 'itemaddproductname': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class CustomerReviewRanking(APIView):
    def get(self, request, format=None):
        customer = []
        with connections['default'].cursor() as c:
            sql = "SELECT KUNDE.NACHNAME, REZENSION.KUNDENKONTO_ID, COUNT(REZENSION.REZENSION_ID) FROM REZENSION, " \
                  "KUNDENKONTO, KUNDE WHERE REZENSION.KUNDENKONTO_ID = KUNDENKONTO.KUNDENKONTO_ID AND KUNDE.KUNDE_ID " \
                  "= KUNDENKONTO.KUNDE_ID group by REZENSION.KUNDENKONTO_ID, KUNDE.NACHNAME order by COUNT(" \
                  "REZENSION.REZENSION_ID) DESC;"
            c.execute(sql)
            for row in c:
                customer.append({'customer-name': row[0], 'customer-account-id': row[1], 'review-count': row[2]})
            return Response({'customer-review-ranking': customer})


class CustomerRevenueRanking(APIView):
    def get(self, request, format=None):
        customer = []
        with connections['default'].cursor() as c:
            sql = "SELECT KUNDE.NACHNAME, KUNDE.KUNDE_ID, sum(RECHNUNG.SUMME_BRUTTO) FROM KUNDE, WARENKORB, BESTELLPOSITION, BESTELLUNG, RECHNUNG WHERE KUNDE.KUNDE_ID = WARENKORB.KUNDE_ID AND WARENKORB.WARENKORB_ID = BESTELLUNG.WARENKORB_ID AND BESTELLUNG.BESTELLUNG_ID = RECHNUNG.RECHNUNG_ID AND BESTELLUNG.BESTELLUNG_ID= BESTELLPOSITION.BESTELLUNG_ID group by KUNDE.NACHNAME, KUNDE.KUNDE_ID order by sum(RECHNUNG.SUMME_BRUTTO) DESC;"
            c.execute(sql)
            for row in c:
                customer.append({'customer-name': row[0], 'customer-account-id': row[1], 'revenue-sum': row[2]})
            return Response({'customer-revenue-ranking': customer})


class TopRatedProducts(APIView):
    def get(self, request, format=None):
        products = []
        with connections['default'].cursor() as c:
            sql = "SELECT REZENSION.PRODUKT_ID, RANKING, count(REZENSION.PRODUKT_ID) FROM PRODUKT, REZENSION WHERE PRODUKT.PRODUKT_ID = REZENSION.PRODUKT_ID GROUP BY REZENSION.PRODUKT_ID, RANKING ORDER BY -RANKING ASC, count(REZENSION.PRODUKT_ID) ASC;"
            c.execute(sql)
            for row in c:
                products.append({'product-id': row[0], 'ranking': row[1], 'ranking-count-for-product': row[2]})
        return Response({'top-rated-products': products})


class OrderCountDay(APIView):
    def get(self, request, format=None):
        with connections['default'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between sysdate - 1 AND sysdate;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCountWeek(APIView):
    def get(self, request, format=None):
        with connections['default'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between sysdate - 7 AND sysdate;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCountMonth(APIView):
    def get(self, request, format=None):
        with connections['default'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between add_months(trunc(sysdate, 'mm'), -1) and last_day(add_months(trunc(sysdate, 'mm'), -1));"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCount(APIView):
    def get(self, request, format=None):
        with connections['default'].cursor() as c:
            sql = "select COUNT(BESTELLUNG_ID) FROM BESTELLPOSITION;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderRevenueDay(APIView):
    def get(self, request, format=None):
        days = 1
        with connections['default'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG where RECHNUNGSDATUM between " \
                  "sysdate - " + str(days) + " AND sysdate"
            c.execute(sql)
            for row in c:
                if row[0] is None:
                    return Response({'order-revenue': 0})
                return Response({'order-revenue': row[0]})


class OrderRevenueWeek(APIView):
    def get(self, request, format=None):
        days = 7
        with connections['default'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG where RECHNUNGSDATUM between " \
                  "sysdate - " + str(days) + " AND sysdate"
            c.execute(sql)
            for row in c:
                if row[0] is None:
                    return Response({'order-revenue': 0})
                return Response({'order-revenue': row[0]})


class OrderRevenueMonth(APIView):
    def get(self, request, format=None):
        days = 30
        with connections['default'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG where RECHNUNGSDATUM between " \
                  "sysdate - " + str(days) + " AND sysdate"
            c.execute(sql)
            for row in c:
                if row[0] is None:
                    return Response({'order-revenue': 0})
                return Response({'order-revenue': row[0]})


class OrderRevenue(APIView):
    def get(self, request, format=None):
        with connections['default'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG"
            c.execute(sql)
            for row in c:
                return Response({'order-revenue': row[0]})
            return Response({'order-revenue': 0})


def beautify_date_string(string: str):
    lst = string.split("-")
    return f"{lst[2]}/{lst[1]}/{lst[0][2:]}"


def get_data_with_aggregated_dates(sql: str, days: int):
    rdates = []
    values = []

    with connections['default'].cursor() as c:
        c.execute(sql)
        cursor_data = c.fetchall()

    cdates = [elem[0].date() for elem in cursor_data]
    if len(cdates) == 0:
        rdates = [date.today() - timedelta(i) for i in range(days)]
        for i in range(days):
            values.append(i)
    else:
        cdate_index = 0
        current_date = date.today() - timedelta(days)
        while len(values) < days:
            if len(cdates) > cdate_index:
                while cdates[cdate_index] != current_date:
                    rdates.append(beautify_date_string(str(current_date)))
                    values.append(0)
                    current_date = current_date + timedelta(1)
                if cdates[cdate_index] == current_date:
                    rdates.append(beautify_date_string(str(current_date)))
                    values.append(cursor_data[cdate_index][1])
                    current_date = current_date + timedelta(1)
                    cdate_index += 1
            else:
                rdates.append(beautify_date_string(str(current_date)))
                values.append(0)
                current_date = current_date + timedelta(1)
    return [rdates, values]


def get_revenue_sql_statement(days: int) -> str:
    return "select TRUNC(RECHNUNGSDATUM), sum(SUMME_BRUTTO) as ANZAHL_KAEUFE from RECHNUNG where " \
           "RECHNUNGSDATUM between sysdate - " + str(
        days) + " AND sysdate group by TRUNC(RECHNUNGSDATUM) order by TRUNC(RECHNUNGSDATUM)"


def get_orders_sql_statement(days: int) -> str:
    return "select TRUNC(RECHNUNGSDATUM), count(RECHNUNG_ID) as ANZAHL_KAEUFE from RECHNUNG where " \
           "RECHNUNGSDATUM between sysdate - " + str(
        days) + " AND sysdate group by TRUNC(RECHNUNGSDATUM) order by TRUNC(RECHNUNGSDATUM)"


class OrdersOneHundredDays(APIView):
    def get(self, request, format=None):
        days = 100
        sql = get_orders_sql_statement(days=days)
        return Response({'orders': get_data_with_aggregated_dates(sql, days)})


class OrdersWeek(APIView):
    def get(self, request, format=None):
        days = 7
        sql = get_orders_sql_statement(days=days)
        return Response({'orders': get_data_with_aggregated_dates(sql, days)})


class RevenueOneHundredDays(APIView):
    def get(self, request, format=None):
        days = 100
        sql = get_revenue_sql_statement(days=days)
        return Response({'revenue': get_data_with_aggregated_dates(sql, days)})


class RevenueWeek(APIView):
    def get(self, request, format=None):
        days = 7
        sql = get_revenue_sql_statement(days=days)
        return Response({'revenue': get_data_with_aggregated_dates(sql, days)})


class TopSellerProducts(APIView):
    def get(self, request, format=None):
        products = []
        with connections['default'].cursor() as c:
            sql = "SELECT BESTELLPOSITION.PRODUKT_ID, COUNT(BESTELLPOSITION.PRODUKT_ID), SUM(BESTELLPOSITION.MENGE) FROM BESTELLPOSITION, BESTELLUNG WHERE BESTELLPOSITION.BESTELLUNG_ID = BESTELLUNG.BESTELLUNG_ID group by BESTELLPOSITION.PRODUKT_ID;"
            c.execute(sql)
            for row in c:
                products.append({'product-id': row[0], 'number-of-sold': (row[1] * row[2])})
        return Response({'top-seller-products': sorted(products, key=itemgetter('number-of-sold'), reverse=True)})


class LoginCountDay(APIView):
    def get(self, request, format=None):
        days = 1
        return Response({'logins': login_count(days=days)})


class LoginCountWeek(APIView):
    def get(self, request, format=None):
        days = 7
        return Response({'logins': login_count(days=days)})


class LoginCountMonth(APIView):
    def get(self, request, format=None):
        days = 30
        return Response({'logins': login_count(days=days)})


def login_count(days: int):
    with connections['default'].cursor() as c:
        sql = "select COUNT(ID) from AUTH_USER where LAST_LOGIN between " \
              "sysdate - " + str(days) + " AND sysdate"
        c.execute(sql)
        for row in c:
            if row[0] is None:
                return 0
            return row[0]


class OrderStatusCanceledDay(APIView):
    def get(self, request, format=None):
        days = 1
        return Response({'status-canceled': order_status_canceled(days=days)})


class OrderStatusCanceledWeek(APIView):
    def get(self, request, format=None):
        days = 7
        return Response({'status-canceled': order_status_canceled(days=days)})


class OrderStatusCanceledMonth(APIView):
    def get(self, request, format=None):
        days = 30
        return Response({'status-canceled': order_status_canceled(days=days)})


class OrderStatusCompletedDay(APIView):
    def get(self, request, format=None):
        days = 1
        return Response({'status-completed': order_status_completed(days=days)})


class OrderStatusCompletedWeek(APIView):
    def get(self, request, format=None):
        days = 7
        return Response({'status-completed': order_status_completed(days=days)})


class OrderStatusCompletedMonth(APIView):
    def get(self, request, format=None):
        days = 30
        return Response({'status-completed': order_status_completed(days=days)})


def order_status_completed(days: int):
    with connections['default'].cursor() as c:
        sql = "Select COUNT(BESTELLUNG_ID) FROM BESTELLUNG WHERE STATUS = 'Abgeschlossen' AND BESTELLDATUM between sysdate - " + str(
            days) + " AND sysdate"
        c.execute(sql)
        for row in c:
            if row[0] is None:
                return 0
            return row[0]


def order_status_canceled(days: int):
    with connections['default'].cursor() as c:
        sql = "Select COUNT(BESTELLUNG_ID) FROM BESTELLUNG WHERE STATUS = 'Storniert' AND BESTELLDATUM between sysdate - " + str(
            days) + " AND sysdate"
        c.execute(sql)
        for row in c:
            if row[0] is None:
                return 0
            return row[0]
