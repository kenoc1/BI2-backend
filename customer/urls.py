from django.urls import path

from customer import views

urlpatterns = [
    path('user/register/', views.register),
    path('user/information/', views.UserInformation.as_view()),
]