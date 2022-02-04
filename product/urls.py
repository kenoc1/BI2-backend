from django.urls import path, include

from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    path('products/<slug:family_slug>/pg=<int:page_index>', views.FamilyDetail.as_view()),
    path('one/', views.OneProduct.as_view()),
]