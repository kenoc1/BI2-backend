from django.contrib import admin

from .models import ProductSubcategory, Product

admin.site.register(ProductSubcategory)
admin.site.register(Product)