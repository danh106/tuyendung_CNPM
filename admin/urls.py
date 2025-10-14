from django.contrib import admin
from django.urls import path
from admin import views

urlpatterns = [
    path("admin", views.index),
]