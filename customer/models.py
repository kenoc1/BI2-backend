from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Address(models.Model):
    address_id = models.AutoField(primary_key=True, db_column='adresse_id')
    country = models.CharField(max_length=40, db_column='land')
    postcode = models.CharField(max_length=10, db_column='plz')
    place = models.CharField(max_length=40, db_column='ort')
    street = models.CharField(max_length=40, db_column='strasse')
    house_number = models.CharField(max_length=10, db_column='hausnummer')
    federal_state = models.CharField(max_length=255, blank=True, null=True, db_column='bundesland')

    class Meta:
        managed = False
        db_table = 'adresse'

    def __str__(self):
        return str(self.country) + ';' + str(self.postcode) + ';' + str(self.place) + ';' + str(self.street)


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, db_column='kunde_id')
    salutation = models.CharField(max_length=20, blank=True, null=True, db_column='anrede')
    firstname = models.CharField(max_length=100, db_column='vorname')
    lastname = models.CharField(max_length=100, db_column='nachname')
    email = models.CharField(max_length=100, db_column='email')
    birth_date = models.DateField(blank=True, null=True, db_column='geburtsdatum')
    django_user = models.FloatField(db_column='django_user')

    class Meta:
        managed = False
        db_table = 'kunde'

    def __str__(self):
        return str(self.firstname) + ' , ' + str(self.lastname)


class CustomerAddress(models.Model):
    customer_address_id = models.AutoField(primary_key=True, db_column='kunde_adresse_id')
    address = models.ForeignKey(Address, models.DO_NOTHING, blank=True, null=True, db_column='adresse_id')
    customer = models.ForeignKey(Customer, models.DO_NOTHING, blank=True, null=True, db_column='kunde_id')
    address_type = models.CharField(max_length=100, blank=True, null=True, db_column='adressart')

    class Meta:
        managed = False
        db_table = 'kunde_adresse'
