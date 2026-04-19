from django.urls import path
from django.contrib import admin
from home import views



urlpatterns = [
    path("",views.index, name='index'),
    path("orders",views.orders, name='orders'),
    path("reports", views.reports, name='reports'),
]