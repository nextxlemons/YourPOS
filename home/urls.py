from django.urls import path
from django.contrib import admin
from home import views



urlpatterns = [
    path("", views.index, name='index'),
    path("home", views.home, name='home'),
    path("orders", views.orders, name='orders'),

    path("createorders", views.createorders, name='createorders'),
    path('createorders/<int:table_id>/', views.createorders, name='createorders'),
    path('category/<int:category_id>/items/', views.category_items, name='category_items'),
    path('order/<int:order_id>/add-item/', views.add_order_item, name='add_order_item'),
    path('order-item/<int:item_id>/update/', views.update_order_item, name='update_order_item'),
    path('order/<int:order_id>/settle/', views.settle_order, name='settle_order'),

    path("managecategories", views.managecategories, name='managecategories'),
    path("manageitems", views.manageitems, name='manageitems'),
    path("additems", views.additems, name='additems'),
    path("edititem", views.edititem, name = 'edititem'),
    path("edititem/<int:pk>", views.edititem, name='edititem'),

    path('orderhistory/', views.orderhistory, name='orderhistory'),
    path('salesreport/', views.salesreport, name='salesreport'),


]