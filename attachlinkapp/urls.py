from .views import index
from django import views
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path("", index, name="index")
]