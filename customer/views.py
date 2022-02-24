from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render

from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response


@api_view(['POST'])
def login(request):
    print("dffae")
    print(request.data)
