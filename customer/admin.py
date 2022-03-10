from django.contrib import admin

# Register your models here.
from .models import Address, Customer, CustomerAddress

admin.site.register(Address)
admin.site.register(Customer)
admin.site.register(CustomerAddress)
