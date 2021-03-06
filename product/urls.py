from django.urls import path, include, re_path
from django.conf.urls import url, include
from product import views

urlpatterns = [
    path('latest-products/', views.LatestProductsList.as_view()),
    path('products/search/', views.search),
    path('product/<slug:product_slug>/', views.ProductDetail.as_view()),
    re_path(r'^products/(?P<family_slug>[a-z_]+)/$', views.FamilyDetail.as_view()),
    # path('products/<slug:family_slug>/', views.FamilyDetail.as_view()),
    re_path(r'^products/(?P<family_slug>[a-z_]+)/(?P<division_slug>[a-z_]+)/$', views.DivisionDetail.as_view()),
    # path('products/<slug:family_slug>/<slug:division_slug>/', views.DivisionDetail.as_view()),
    path('categories/', views.Categories.as_view()),
    path('favoritProduct/', views.FavoriteProduct.as_view()),
    url(r'^products/(?P<family_slug>[a-z0-9-+()]+)/$', views.FamilyDetail.as_view()),
    path('one/', views.OneProduct.as_view()),
    path('personal-recommendations/', views.PersonalRecommendationsList.as_view()),
    path('cart-recommendations/', views.CartRecommendationsList.as_view()),
    path('favoritProduct/<slug:family_slug>/', views.FavoriteProductByFamilySlug.as_view()),

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

    path('history-orders-100/', views.OrdersOneHundredDays.as_view()),
    path('history-orders-7/', views.OrdersWeek.as_view()),
    path('history-revenue-100/', views.RevenueOneHundredDays.as_view()),
    path('history-revenue-7/', views.RevenueWeek.as_view()),
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
