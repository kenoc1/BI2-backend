from django.urls import path

from customer import views

urlpatterns = [
    path('user/login/', views.login),
]