from django.urls import path
from django.contrib import admin
from home import views

from .views import signup_view, login_view, logout_view


urlpatterns = [


    path('', login_view, name='login'), # login as landing page
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path("home", views.home, name='home'),
    path("orders", views.orders, name='orders'),

    path("createorders", views.createorders, name='createorders'),
    path('createorders/<int:table_id>/', views.createorders, name='createorders'),

    path("managecategories", views.managecategories, name='managecategories'),
    path("manageitems", views.manageitems, name='manageitems'),
    path("additems", views.additems, name='additems'),
    path("edititem", views.edititem, name = 'edititem'),
    path("edititem/<int:pk>", views.edititem, name='edititem'),

    path('orderhistory/', views.orderhistory, name='orderhistory'),
    path('salesreport/', views.salesreport, name='salesreport'),
    path('settings/', views.settings, name='settings'),
]