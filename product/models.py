from io import BytesIO
from PIL import Image

from django.core.files import File
from django.db import models


class ProductFamily(models.Model):
    product_family_id = models.FloatField(primary_key=True, db_column="produkt_familie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        managed = False
        db_table = 'produkt_familie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/{self.slug}/'


class ProductDivision(models.Model):
    product_division_id = models.FloatField(primary_key=True, db_column="produkt_sparte_id")
    product_family = models.ForeignKey(ProductFamily, on_delete=models.DO_NOTHING, blank=True, null=True, db_column="produkt_familie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        managed = False
        db_table = 'produkt_sparte'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/{self.slug}/'


class ProductCategory(models.Model):
    product_category_id = models.FloatField(primary_key=True, db_column="produkt_kategorie_id")
    Product_division = models.ForeignKey(ProductDivision, on_delete=models.DO_NOTHING, blank=True, null=True, db_column="produkt_sparte_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        managed = False
        db_table = 'produkt_kategorie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/{self.slug}/'


class ProductSubcategory(models.Model):
    product_subcategory_id = models.FloatField(primary_key=True, db_column="produkt_subkategorie_id")
    product_category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, blank=True, null=True, db_column="produkt_kategorie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        ordering = ('description',)
        db_table = 'produkt_subkategorie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/{self.slug}/'


class Product(models.Model):
    product_id = models.FloatField(primary_key=True, db_column="produkt_id", default=1)
    category = models.ForeignKey(ProductSubcategory, related_name='products', on_delete=models.CASCADE, db_column="produktklasse_id")
    name = models.CharField(db_column="proukt_name", max_length=150)
    slug = models.SlugField()
    description = models.CharField(max_length=500, blank=True, null=True, db_column="produktbeschreibung")
    price = models.FloatField(db_column="listenverkaufspreis")
    image = 'https://pixabay.com/get/ga8ab573925eed1f5f1a26cd2d6eca8ad7d51f8f956db730f4ffa532805d9bb3a0de55d7a404754325c12b9c4c206a936a2d2f63a1307497109959cc5031f389c919cde13485a21189872d8158a42e00b_1920.jpg'
    thumbnail = 'https://pixabay.com/get/ga8ab573925eed1f5f1a26cd2d6eca8ad7d51f8f956db730f4ffa532805d9bb3a0de55d7a404754325c12b9c4c206a936a2d2f63a1307497109959cc5031f389c919cde13485a21189872d8158a42e00b_1920.jpg'
    # date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ordering = ('-date_added',)
        db_table = 'produkt'
        managed = 'true'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/{self.category.slug}/{self.slug}/'

    def get_image(self):
        return self.image

    def get_thumbnail(self):
        return self.thumbnail
        # if self.thumbnail:
        #     return 'http://127.0.0.1:8000' + self.thumbnail.url
        # else:
        #     if self.image:
        #         self.thumbnail = self.make_thumbnail(self.image)
        #         self.save()
        #
        #         return 'http://127.0.0.1:8000' + self.thumbnail.url
        #     else:
        #         return ''
    #
    # def make_thumbnail(self, image, size=(300, 200)):
    #     img = Image.open(image)
    #     img.convert('RGB')
    #     img.thumbnail(size)
    #
    #     thumb_io = BytesIO()
    #     img.save(thumb_io, 'JPEG', quality=85)
    #
    #     thumbnail = File(thumb_io, name=image.name)
    #
    #     return thumbnail
