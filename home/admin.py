from django.contrib import admin
from home.models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order

# Register your models here.
admin.site.register(TableInfo)
admin.site.register(MenuCategory)
admin.site.register(MenuItem)
admin.site.register(MenuVariant)
admin.site.register(Order)
