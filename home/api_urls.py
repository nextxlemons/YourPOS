from django.urls import path
from . import api_views

urlpatterns = [
    # Auth
    path('auth/signup/', api_views.SignupAPI.as_view(), name='api-signup'),
    path('auth/login/', api_views.LoginAPI.as_view(), name='api-login'),
    path('auth/logout/', api_views.LogoutAPI.as_view(), name='api-logout'),
    path('auth/status/', api_views.SessionStatusAPI.as_view(), name='api-status'),


    # Tables
    path('tables/', api_views.TableListAPI.as_view(), name='api-tables'),
    path('tables/create/', api_views.TableCreateAPI.as_view(), name='api-table-create'),

    # Categories
    path('categories/', api_views.MenuCategoryListAPI.as_view(), name='api-categories'),
    path('categories/create/', api_views.MenuCategoryCreateAPI.as_view(), name='api-category-create'),
    path('categories/<int:pk>/update/', api_views.MenuCategoryUpdateAPI.as_view(), name='api-category-update'),
    path('categories/<int:pk>/delete/', api_views.MenuCategoryDeleteAPI.as_view(), name='api-category-delete'),

    # Menu items
    path('menu-items/', api_views.MenuItemListAPI.as_view(), name='api-menu-items'),
    path('menu-items/<int:pk>/', api_views.MenuItemDetailAPI.as_view(), name='api-menu-item-detail'),
    path('menu-items/create/', api_views.MenuItemCreateAPI.as_view(), name='api-menu-item-create'),
    path('menu-items/<int:pk>/update/', api_views.MenuItemUpdateAPI.as_view(), name='api-menu-item-update'),
    path('menu-items/<int:pk>/delete/', api_views.MenuItemDeleteAPI.as_view(), name='api-menu-item-delete'),

    # Orders
    path('orders/<int:pk>/', api_views.OrderDetailAPI.as_view(), name='api-order-detail'),
    path('tables/<int:table_id>/order/', api_views.CreateOrGetOrderAPI.as_view(), name='api-order-create'),
    path('orders/<int:order_id>/add-item/', api_views.AddOrderItemAPI.as_view(), name='api-add-item'),
    path('order-items/<int:item_id>/update/', api_views.UpdateOrderItemAPI.as_view(), name='api-update-item'),
    path('orders/<int:order_id>/settle/', api_views.SettleOrderAPI.as_view(), name='api-settle'),

    # Bills / reports
    path('bills/', api_views.BillListAPI.as_view(), name='api-bills'),
    path('bills/<int:pk>/', api_views.BillDetailAPI.as_view(), name='api-bill-detail'),
    path('reports/sales/', api_views.SalesReportAPI.as_view(), name='api-sales-report'),
]