from django.contrib import admin
from home.models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill, Cafe
# Register your models here.

admin.site.register(Cafe)
# admin can not access this tables


# admin.site.register(TableInfo)
# admin.site.register(MenuCategory)
# admin.site.register(MenuItem)
# admin.site.register(MenuVariant)
# admin.site.register(Order)
# admin.site.register(OrderItem)
# admin.site.register(Bill)
