from django.db import models


class ProductFamily(models.Model):
    product_family_id = models.FloatField(primary_key=True, db_column="produkt_familie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        ordering = ('description',)
        db_table = 'produkt_familie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'products/{self.slug}/'


class ProductDivision(models.Model):
    product_division_id = models.FloatField(primary_key=True, db_column="produkt_sparte_id")
    product_family = models.ForeignKey(ProductFamily, related_name="divisions", on_delete=models.DO_NOTHING, blank=True,
                                       null=True, db_column="produkt_familie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        ordering = ('description',)
        db_table = 'produkt_sparte'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/products/{self.product_family.slug}/{self.slug}/'


class ProductCategory(models.Model):
    product_category_id = models.FloatField(primary_key=True, db_column="produkt_kategorie_id")
    product_division = models.ForeignKey(ProductDivision, related_name="categories", on_delete=models.DO_NOTHING,
                                         blank=True, null=True, db_column="produkt_sparte_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        ordering = ('description',)
        db_table = 'produkt_kategorie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/products/{self.product_division.product_family.slug}/{self.product_division.slug}/{self.slug}'


class ProductSubcategory(models.Model):
    product_subcategory_id = models.FloatField(primary_key=True, db_column="produkt_subkategorie_id")
    product_category = models.ForeignKey(ProductCategory, related_name="subcategories", on_delete=models.DO_NOTHING,
                                         blank=True, null=True, db_column="produkt_kategorie_id")
    description = models.CharField(max_length=50, db_column="bezeichnung")
    slug = models.SlugField(default="test")

    class Meta:
        ordering = ('description',)
        db_table = 'produkt_subkategorie'

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return f'/products/{self.product_category.product_division.product_family.slug}/{self.product_category.product_division.slug}/{self.product_category.slug}/{self.slug}/'


class Product(models.Model):
    product_id = models.AutoField(primary_key=True, db_column="produkt_id")
    subcategory = models.ForeignKey(ProductSubcategory, related_name='products', on_delete=models.CASCADE,
                                    db_column="produktklasse_id", blank=True, null=True)
    name = models.CharField(db_column="proukt_name", max_length=150)
    slug = models.SlugField()
    description = models.CharField(max_length=500, blank=True, null=True, db_column="produktbeschreibung")
    price = models.FloatField(db_column="listenverkaufspreis")
    image = models.CharField(db_column="produktbild_link", max_length=1000, blank=True, null=True)
    sku = models.FloatField(db_column="sku", blank=True, null=True)
    evaluation = models.FloatField(db_column="bewertung", blank=True, null=True)
    recycle = models.FloatField(db_column="recyclebar", blank=True, null=True)
    lowfat = models.FloatField(db_column="low_fat", blank=True, null=True)
    mwst = models.FloatField(db_column="mwst_satz")
    discount = models.FloatField(db_column="angebotsrabatt", blank=True, null=True)
    origin = models.FloatField(db_column="datenherkunft_id", blank=True, null=True)
    # date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ordering = ('-date_added',)
        db_table = 'produkt'
        managed = 'true'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/product/{self.slug}/'

    def get_image(self):
        return self.image.split(',')[0]

    def get_thumbnail(self):
        return self.image.split(',')[0]

    def get_price(self):
        return round(self.price, 2)
