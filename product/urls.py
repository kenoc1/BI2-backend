from django.urls import path, include
from django.conf.urls import url, include
from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/$', views.FamilyDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/$(?P<division_slug>[a-z0-9-+()]+)/$', views.DivisionDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/(?P<division_slug>[a-z0-9-+()]+)/(?P<category_slug>[a-z0-9-+()]+)/$', views.CategoryDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/(?P<division_slug>[a-z0-9-+()]+)/(?P<category_slug>[a-z0-9-+()]+)/(?P<subcategory_slug>[a-z0-9-+()]+)/$', views.SubcategoryDetail.as_view()),
    path('categories/', views.Categories.as_view()),
]