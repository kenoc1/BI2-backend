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
    path('order-count-week/', views.OrderCountWeek.as_view()),
    path('order-count-month/', views.OrderCountMonth.as_view()),
    path('order-count/', views.OrderCount.as_view()),

    path('login-count-day/', views.LoginCountDay.as_view()),
    path('login-count-week/', views.LoginCountWeek.as_view()),
    path('login-count-month/', views.LoginCountMonth.as_view()),

    path('order-status-canceled-day/', views.OrderStatusCanceledDay.as_view()),
    path('order-status-canceled-week/', views.OrderStatusCanceledWeek.as_view()),
    path('order-status-canceled-month/', views.OrderStatusCanceledMonth.as_view()),
    path('order-status-completed-day/', views.OrderStatusCompletedDay.as_view()),
    path('order-status-completed-week/', views.OrderStatusCompletedWeek.as_view()),
    path('order-status-completed-month/', views.OrderStatusCompletedMonth.as_view()),

    path('history-orders/', views.OrdersWeek.as_view()),
    path('history-revenue/', views.Revenue.as_view()),
    path('top-seller-products/', views.TopSellerProducts.as_view()),
    path('top-rated-products/', views.TopRatedProducts.as_view()),
    path('customer-review-ranking/', views.CustomerReviewRanking.as_view()),
    path('customer-revenue-ranking/', views.CustomerRevenueRanking.as_view()),
    path('order-revenue-day/', views.OrderRevenueDay.as_view()),
    path('order-revenue-week/', views.OrderRevenueWeek.as_view()),
    path('order-revenue-month/', views.OrderRevenueMonth.as_view()),
    path('order-revenue/', views.OrderRevenue.as_view()),
    path('association-mr/', views.AssociationsMr.as_view()),
    path('association-ms/', views.AssociationsMs.as_view()),
    path('association-order/', views.AssociationsOrder.as_view()),
]
