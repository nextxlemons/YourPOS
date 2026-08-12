from rest_framework import serializers
from .models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill


class MenuVariantSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(source='get_size_display', read_only=True)

    class Meta:
        model = MenuVariant
        fields = ['id', 'size', 'size_display', 'price']


class MenuItemSerializer(serializers.ModelSerializer):
    variants = MenuVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'category', 'category_name', 'is_active', 'variants']


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'is_active']


class TableInfoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TableInfo
        fields = ['table_no', 'status', 'status_display']


class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='variant.item.name', read_only=True)
    size_display = serializers.CharField(source='variant.get_size_display', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'item_name', 'size_display', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    table_no = serializers.IntegerField(source='table.table_no', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'table', 'table_no', 'status', 'created_at', 'items', 'total']


class BillSerializer(serializers.ModelSerializer):
    table_no = serializers.IntegerField(source='table.table_no', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'bill_number', 'table', 'table_no', 'total_amount',
            'payment_method', 'payment_method_display', 'items_summary',
            'note', 'created_at',
        ]
        read_only_fields = fields  # bills are created only via the settle bill only 