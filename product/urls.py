from django.urls import path, include
from django.conf.urls import url, include
from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/$', views.FamilyDetail.as_view()),
    path('one/', views.OneProduct.as_view()),
    path('order-count-day/', views.get_order_count_day()),
    path('order-count-month/', views.get_order_count_month()),
    path('order-count/', views.get_order_count()),
    path('history-orders/', views.get_orders(100)),
    path('history-revenue/', views.get_revenue(100)),
    path('top-seller/', views.get_top_seller()),
]