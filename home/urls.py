from django.urls import path, include
from django.contrib import admin
from home import views

from .views import signup_view, login_view, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('home.api_urls')),

    path('signup/', views.signup_view, name='signup'),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('home/', views.home, name='home'),
    path('orders/', views.orders, name='orders'),
    path('createorders/<int:table_id>/', views.createorders, name='createorders'),

    path('managecategories/', views.managecategories, name='managecategories'),
    path('manageitems/', views.manageitems, name='manageitems'),
    path('additems/', views.additems, name='additems'),
    path('edititem/<int:pk>/', views.edititem, name='edititem'),

    path('orderhistory/', views.orderhistory, name='orderhistory'),
    path('salesreport/', views.salesreport, name='salesreport'),
    path('settings/', views.settings, name='settings'),
]