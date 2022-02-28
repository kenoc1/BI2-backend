from django.urls import path, include
from django.conf.urls import url, include
from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/$', views.FamilyDetail.as_view()),
    path('one/', views.OneProduct.as_view()),
    path('order-count-day/', views.OrderCountDay.as_view()),
    path('order-count-month/', views.OrderCountMonth.as_view()),
    path('order-count/', views.OrderCount.as_view()),
    path('history-orders/', views.Orders.as_view()),
    path('history-revenue/', views.Revenue.as_view()),
    path('top-seller/', views.TopSeller.as_view()),
]
