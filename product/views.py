import json
import re
from datetime import date, timedelta
from operator import itemgetter

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
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEHERR, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEHERR, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'rule-id': row[0], 'item-base-product-sku': row[2],
                             'item-base-product-name': row[3],
                             'item-add-product-sku': row[5], 'item-add-product-name': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class AssociationsMs(APIView):
    def get(self, request, format=None):
        asso = []
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEFRAU, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOANREDEFRAU, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'rule-id': row[0], 'item-base-product-sku': row[2],
                             'item-base-product-name': row[3],
                             'item-add-product-sku': row[5], 'item-add-product-name': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class AssociationsOrder(APIView):
    def get(self, request, format=None):
        asso = []
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT t1.RULE_ID, t1.PRODUKT_ID, t1.SKU, t1.PROUKT_NAME, t2.PRODUKT_ID, t2.SKU, t2.PROUKT_NAME, t1.CONFIDENCE, t1.LIFT, t1.SUPPORT FROM (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOBESTELLUNG, PRODUKT WHERE REPLACE(REPLACE(ITEMS_BASE, '{', ''), '}', '') = PRODUKT.SKU) t1 LEFT JOIN (SELECT PRODUKT_ID, SKU, PROUKT_NAME, RULE_ID, ITEMS_BASE, ITEMS_ADD, CONFIDENCE, LIFT, SUPPORT FROM ASSOBESTELLUNG, PRODUKT WHERE REPLACE(REPLACE(ITEMS_ADD, '{', ''), '}', '') = PRODUKT.SKU) t2 ON (t1.RULE_ID=t2.RULE_ID);"
            c.execute(sql)
            for row in c:
                asso.append({'rule-id': row[0], 'item-base-product-sku': row[2],
                             'item-base-product-name': row[3],
                             'item-add-product-sku': row[5], 'item-add-product-name': row[6], 'confidence': row[7],
                             'lift': row[8], 'support': row[9]})
            return Response({'asso-order': delete_duplicates(asso)})


class CustomerReviewRanking(APIView):
    def get(self, request, format=None):
        customer = []
        with connections['oracle_db'].cursor() as c:
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
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT KUNDE.NACHNAME, KUNDE.KUNDE_ID, sum(RECHNUNG.SUMME_BRUTTO) FROM KUNDE, WARENKORB, BESTELLPOSITION, BESTELLUNG, RECHNUNG WHERE KUNDE.KUNDE_ID = WARENKORB.KUNDE_ID AND WARENKORB.WARENKORB_ID = BESTELLUNG.WARENKORB_ID AND BESTELLUNG.BESTELLUNG_ID = RECHNUNG.RECHNUNG_ID AND BESTELLUNG.BESTELLUNG_ID= BESTELLPOSITION.BESTELLUNG_ID group by KUNDE.NACHNAME, KUNDE.KUNDE_ID order by sum(RECHNUNG.SUMME_BRUTTO) DESC;"
            c.execute(sql)
            for row in c:
                customer.append({'customer-name': row[0], 'customer-account-id': row[1], 'revenue-sum': row[2]})
            return Response({'customer-revenue-ranking': customer})


class TopRatedProducts(APIView):
    def get(self, request, format=None):
        products = []
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT REZENSION.PRODUKT_ID, RANKING, count(REZENSION.PRODUKT_ID) FROM PRODUKT, REZENSION WHERE PRODUKT.PRODUKT_ID = REZENSION.PRODUKT_ID GROUP BY REZENSION.PRODUKT_ID, RANKING ORDER BY -RANKING ASC, count(REZENSION.PRODUKT_ID) ASC;"
            c.execute(sql)
            for row in c:
                products.append({'product-id': row[0], 'ranking': row[1], 'ranking-count-for-product': row[2]})
        return Response({'top-rated-products': products})


class OrderCountDay(APIView):
    def get(self, request, format=None):
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between sysdate - 1 AND sysdate;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCountWeek(APIView):
    def get(self, request, format=None):
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between sysdate - 7 AND sysdate;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCountMonth(APIView):
    def get(self, request, format=None):
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT COUNT(Distinct BESTELLUNG_ID) FROM BESTELLUNG Where BESTELLDATUM between add_months(trunc(sysdate, 'mm'), -1) and last_day(add_months(trunc(sysdate, 'mm'), -1));"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderCount(APIView):
    def get(self, request, format=None):
        with connections['oracle_db'].cursor() as c:
            sql = "select COUNT(BESTELLUNG_ID) FROM BESTELLPOSITION;"
            c.execute(sql)
            for row in c:
                return Response({'orders': row[0]})
            return Response({'orders': 0})


class OrderRevenueDay(APIView):
    def get(self, request, format=None):
        days = 1
        with connections['oracle_db'].cursor() as c:
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
        with connections['oracle_db'].cursor() as c:
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
        with connections['oracle_db'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG where RECHNUNGSDATUM between " \
                  "sysdate - " + str(days) + " AND sysdate"
            c.execute(sql)
            for row in c:
                if row[0] is None:
                    return Response({'order-revenue': 0})
                return Response({'order-revenue': row[0]})


class OrderRevenue(APIView):
    def get(self, request, format=None):
        with connections['oracle_db'].cursor() as c:
            sql = "select sum(SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO from RECHNUNG"
            c.execute(sql)
            for row in c:
                return Response({'order-revenue': row[0]})
            return Response({'order-revenue': 0})


class OrdersWeek(APIView):

    @staticmethod
    def beautify_date_string(string: str):
        lst = string.split("-")
        return f"{lst[2]}/{lst[1]}/{lst[0][2:]}"

    def get(self, request, format=None):
        days = 7
        orders = []
        rdates = []
        values = []

        with connections['oracle_db'].cursor() as c:
            sql = "select TRUNC(RECHNUNGSDATUM), count(RECHNUNG_ID) as ANZAHL_KAEUFE from RECHNUNG where " \
                  "RECHNUNGSDATUM between sysdate - " + str(
                days) + " AND sysdate group by TRUNC(RECHNUNGSDATUM) order by TRUNC(RECHNUNGSDATUM)"
            c.execute(sql)
            cursor_data = c.fetchall()

        cdates = [elem[0].date() for elem in cursor_data]

        if len(cdates) == 0:
            rdates = [date.today() - timedelta(i) for i in [0, 1, 2, 3, 4, 5, 6, 7]]
            values = [0, 0, 0, 0, 0, 0, 0]
        else:
            x = 0
            current_date = date.today() - timedelta(7)
            while len(values) < 7:
                while cdates[x] != current_date:
                    rdates.append(self.beautify_date_string(str(current_date)))
                    values.append(0)
                    current_date = current_date + timedelta(1)
                if cdates[x] == current_date:
                    rdates.append(self.beautify_date_string(str(current_date)))
                    values.append(cursor_data[x][1])
                    x += 1
        orders.append(rdates)
        orders.append(values)
        return Response({'orders': orders})


class Revenue(APIView):
    def get(self, request, format=None):
        days = 100
        revenue = []
        with connections['oracle_db'].cursor() as c:
            sql = "select TRUNC(RECHNUNGSDATUM), sum(SUMME_BRUTTO) as ANZAHL_KAEUFE from RECHNUNG where " \
                  "RECHNUNGSDATUM between sysdate - " + str(days) + " AND sysdate group by TRUNC(RECHNUNGSDATUM)"
            c.execute(sql)
            for row in c:
                revenue.append([row[0], row[1]])
                # revenue.append({'date': row[0], 'revenue-sum': row[1]})
        return Response({'revenue': revenue})


class TopSellerProducts(APIView):
    def get(self, request, format=None):
        products = []
        with connections['oracle_db'].cursor() as c:
            sql = "SELECT BESTELLPOSITION.PRODUKT_ID, COUNT(BESTELLPOSITION.PRODUKT_ID), SUM(BESTELLPOSITION.MENGE) FROM BESTELLPOSITION, BESTELLUNG WHERE BESTELLPOSITION.BESTELLUNG_ID = BESTELLUNG.BESTELLUNG_ID group by BESTELLPOSITION.PRODUKT_ID;"
            c.execute(sql)
            for row in c:
                products.append({'product-id': row[0], 'number-of-sold': (row[1] * row[2])})
        return Response({'top-seller-products': sorted(products, key=itemgetter('number-of-sold'), reverse=True)})


class LoginCountDay(APIView):
    def get(self, request, format=None):
        days = 1
        return Response({'order-revenue': login_count(days=days)})


class LoginCountWeek(APIView):
    def get(self, request, format=None):
        days = 7
        return Response({'order-revenue': login_count(days=days)})


class LoginCountMonth(APIView):
    def get(self, request, format=None):
        days = 30
        return Response({'order-revenue': login_count(days=days)})


def login_count(days: int):
    with connections['oracle_db'].cursor() as c:
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
    with connections['oracle_db'].cursor() as c:
        sql = "Select COUNT(BESTELLUNG_ID) FROM BESTELLUNG WHERE STATUS = 'Abgeschlossen' AND BESTELLDATUM between sysdate - " + str(days) + " AND sysdate"
        c.execute(sql)
        for row in c:
            if row[0] is None:
                return 0
            return row[0]


def order_status_canceled(days: int):
    with connections['oracle_db'].cursor() as c:
        sql = "Select COUNT(BESTELLUNG_ID) FROM BESTELLUNG WHERE STATUS = 'Storniert' AND BESTELLDATUM between sysdate - " + str(days) + " AND sysdate"
        c.execute(sql)
        for row in c:
            if row[0] is None:
                return 0
            return row[0]
