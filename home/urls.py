from django.urls import path
from django.contrib import admin
from home import views



urlpatterns = [
    path("",views.index, name='index'),
    path("orders",views.orders, name='orders'),
    path("reports", views.reports, name='reports'),
    path("managecategories", views.managecategories, name='managecategories'),
    path("manageitems", views.manageitems, name='manageitems'),
    path("additems", views.additems, name='additems'),
    path("edititem", views.edititem, name = 'edititem'),
    path('edititem/<int:pk>', views.edititem, name='edititem'),

]