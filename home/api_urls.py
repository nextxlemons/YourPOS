from django.urls import path
from . import api_views

urlpatterns = [
    path('tables/', api_views.TableListAPI.as_view(), name='api-tables'),
    path('categories/', api_views.MenuCategoryListAPI.as_view(), name='api-categories'),
    path('menu-items/', api_views.MenuItemListAPI.as_view(), name='api-menu-items'),
    path('orders/<int:pk>/', api_views.OrderDetailAPI.as_view(), name='api-order-detail'),
    path('orders/<int:order_id>/add-item/', api_views.AddOrderItemAPI.as_view(), name='api-add-item'),
    path('orders/<int:order_id>/settle/', api_views.SettleOrderAPI.as_view(), name='api-settle'),
    path('bills/', api_views.BillListAPI.as_view(), name='api-bills'),
    path('reports/sales/', api_views.SalesReportAPI.as_view(), name='api-sales-report'),
]