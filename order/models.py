from django.contrib.auth.models import User
from django.db import models

from product.models import Product
from customer.models import Customer


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True, db_column='warenkorb_id')
    customer = models.ForeignKey(Customer, models.DO_NOTHING, blank=True, null=True, db_column='kunde_id')
    total_price = models.FloatField(db_column='gesamtpreis')
    total_quantity = models.FloatField(blank=True, null=True, db_column='gesamtmenge')

    class Meta:
        managed = False
        db_table = 'warenkorb'


class CartProduct(models.Model):
    cart_product_id = models.FloatField(primary_key=True, db_column='warenkorb_produkt_id')
    cart = models.ForeignKey(Cart, models.DO_NOTHING, db_column='warenkorb_id')
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='produkt_id')
    quantity = models.FloatField(db_column='menge')

    class Meta:
        managed = False
        db_table = 'warenkorb_produkt'


class Order(models.Model):
    order_id = models.AutoField(primary_key=True, db_column='bestellung_id')
    cart = models.ForeignKey(Cart, models.DO_NOTHING, blank=True, null=True, db_column='warenkorb_id')
    order_date = models.DateTimeField(db_column='bestelldatum')
    order_status = models.CharField(db_column='status', max_length=30)
    total_quantity = models.FloatField(db_column='gesamtmenge')
    origin = models.FloatField(db_column="datenherkunft_id", blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bestellung'

    def __str__(self):
        return self.order_id


class PaymentMethod(models.Model):
    payment_id = models.AutoField(primary_key=True, db_column='zahlungsart_id')
    name = models.CharField(max_length=100, db_column='bezeichnung')

    class Meta:
        managed = False
        db_table = 'zahlungsart'

    def __str__(self):
        return self.name


class PaymentMethodOrder(models.Model):
    customer_address_id = models.AutoField(primary_key=True, db_column='ZAHLUNGSART_BESTELLUNG_ID')
    payment_method = models.ForeignKey(PaymentMethod, models.DO_NOTHING, blank=True, null=True, db_column='zahlungsart_id')
    order = models.ForeignKey(Order, models.DO_NOTHING, blank=True, null=True, db_column='bestellung_id')

    class Meta:
        managed = False
        db_table = 'zahlungsart_bestellung'


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True, db_column='bestellposition_id')
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='produkt_id')
    order = models.ForeignKey(Order, models.DO_NOTHING, db_column='bestellung_id')
    quantity = models.FloatField(db_column='menge')

    class Meta:
        managed = False
        db_table = 'bestellposition'

    def __str__(self):
        return '%s' % self.order_item_id


class Bill(models.Model):
    bill_id = models.AutoField(primary_key=True, db_column='rechnung_id')
    order = models.ForeignKey(Order, models.DO_NOTHING, db_column='bestellung_id')
    billing_date = models.DateTimeField(db_column='rechnungsdatum')
    total_gross = models.FloatField(db_column='summe_brutto')
    total_net = models.FloatField(db_column='summe_netto')

    class Meta:
        managed = False
        db_table = 'rechnung'

    def __str__(self):
        return self.order_id
