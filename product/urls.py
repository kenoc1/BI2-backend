from django.urls import path, include

from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('products/<slug:family_slug>/<slug:division_slug>/<slug:subcategory_slug>/<slug:product_slug>/', views.ProductDetail.as_view()),
    path('products/<slug:family_slug>/', views.FamilyDetail.as_view()),
]