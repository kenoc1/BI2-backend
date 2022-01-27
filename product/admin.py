from django.contrib import admin

from .models import ProductFamily, ProductDivision, ProductCategory, ProductSubcategory, Product

admin.site.register(ProductFamily)
admin.site.register(ProductDivision)
admin.site.register(ProductCategory)
admin.site.register(ProductSubcategory)
admin.site.register(Product)