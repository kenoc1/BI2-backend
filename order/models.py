from django.contrib.auth.models import User
from django.db import models

from product.models import Product
from customer.models import Customer


class Cart(models.Model):
    cart_id = models.FloatField(primary_key=True, db_column='warenkorb_id')
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
    order_id = models.FloatField(primary_key=True, db_column='bestellung_id')
    # warenkorb = models.ForeignKey('Warenkorb', models.DO_NOTHING, blank=True, null=True, db_column='')
    # rabattcode = models.ForeignKey('Rabattcode', models.DO_NOTHING, blank=True, null=True, db_column='')
    # status = models.CharField(max_length=30, db_column='')
    order_date = models.DateField(db_column='bestelldatum')
    total_quantity = models.FloatField(db_column='gesamtmenge')
    origin = models.FloatField(db_column="datenherkunft_id", blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bestellung'

    def __str__(self):
        return self.order_id


class OrderItem(models.Model):
    order_item_id = models.FloatField(primary_key=True, db_column='bestellposition_id')
    product = models.ForeignKey(Product, models.DO_NOTHING, blank=True, null=True, db_column='produkt')
    order = models.ForeignKey(Order, models.DO_NOTHING, blank=True, null=True, db_column='bestellung')
    quantity = models.FloatField(db_column='menge')

    class Meta:
        managed = False
        db_table = 'bestellposition'

    def __str__(self):
        return '%s' % self.order_item_id


