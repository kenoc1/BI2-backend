from django.urls import path, include, re_path
from django.conf.urls import url, include
from product import views

string1 = "/products/food/eggs"
string1 = "/products/food"

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    re_path(r'^products/(?P<family_slug>[a-z_]+)/$', views.FamilyDetail.as_view()),
    # path('products/<slug:family_slug>/', views.FamilyDetail.as_view()),
    re_path(r'^products/(?P<family_slug>[a-z_]+)/(?P<division_slug>[a-z_]+)/$', views.DivisionDetail.as_view()),
    # path('products/<slug:family_slug>/<slug:division_slug>/', views.DivisionDetail.as_view()),
    path('categories/', views.Categories.as_view()),
]