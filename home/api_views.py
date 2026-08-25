from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill
from .serializers import (
    SignupSerializer, TableInfoSerializer, MenuCategorySerializer,
    MenuItemSerializer, OrderSerializer, BillSerializer,
)


# sign login auth

class SignupAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        user = result['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'cafe_name': result['cafe'].name,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


# table

class TableListAPI(generics.ListAPIView):
    serializer_class = TableInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TableInfo.objects.filter(cafe=self.request.user.cafe).order_by('table_no')


class TableCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        table_no = request.data.get('table_no')
        if not table_no:
            return Response({'error': 'table_no is required'}, status=status.HTTP_400_BAD_REQUEST)

        if TableInfo.objects.filter(cafe=request.user.cafe, table_no=table_no).exists():
            return Response({'error': 'Table already exists'}, status=status.HTTP_400_BAD_REQUEST)

        table = TableInfo.objects.create(cafe=request.user.cafe, table_no=table_no)
        return Response(TableInfoSerializer(table).data, status=status.HTTP_201_CREATED)


# MENU categories

class MenuCategoryListAPI(generics.ListAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MenuCategory.objects.filter(cafe=self.request.user.cafe, is_active=True).order_by('name')


class MenuCategoryCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if MenuCategory.objects.filter(cafe=request.user.cafe, name=name).exists():
            return Response({'error': 'Category already exists'}, status=status.HTTP_400_BAD_REQUEST)

        category = MenuCategory.objects.create(cafe=request.user.cafe, name=name)
        return Response(MenuCategorySerializer(category).data, status=status.HTTP_201_CREATED)


# menu items and all

class MenuItemListAPI(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # scoped through category__cafe since MenuItem has no direct cafe FK
        qs = MenuItem.objects.filter(
            category__cafe=self.request.user.cafe, is_active=True
        ).select_related('category').prefetch_related('variants')

        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


class MenuItemDetailAPI(generics.RetrieveAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MenuItem.objects.filter(category__cafe=self.request.user.cafe)


# orders 
class OrderDetailAPI(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # scoped through table__cafe since Order has no direct cafe FK
        return Order.objects.filter(
            table__cafe=self.request.user.cafe
        ).select_related('table').prefetch_related('items__variant__item')


class CreateOrGetOrderAPI(APIView):
    """Equivalent of your createorders view — opens/reuses the active order for a table."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, table_id):
        table = get_object_or_404(TableInfo, pk=table_id, cafe=request.user.cafe)
        order, created = Order.objects.get_or_create(table=table, status=Order.Status.ACTIVE)
        return Response(OrderSerializer(order).data)


class AddOrderItemAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(
            Order, pk=order_id, status=Order.Status.ACTIVE, table__cafe=request.user.cafe
        )

        variant_id = request.data.get('variant_id')
        # scope variant lookup through item__category__cafe so you can't add another
        # cafe's menu item to your order even by guessing an ID
        variant = get_object_or_404(
            MenuVariant, pk=variant_id, item__category__cafe=request.user.cafe
        )

        order_item, created = OrderItem.objects.get_or_create(
            order=order, variant=variant, defaults={'quantity': 1}
        )
        if not created:
            order_item.quantity += 1
            order_item.save()

        if order.table.status != TableInfo.Status.OCCUPIED:
            order.table.status = TableInfo.Status.OCCUPIED
            order.table.save()

        return Response(OrderSerializer(order).data)


class UpdateOrderItemAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, item_id):
        item = get_object_or_404(
            OrderItem, pk=item_id, order__table__cafe=request.user.cafe
        )
        order = item.order
        action = request.data.get('action')

        if action == 'inc':
            item.quantity += 1
            item.save()
        elif action == 'dec':
            item.quantity -= 1
            if item.quantity <= 0:
                item.delete()
            else:
                item.save()
        elif action == 'remove':
            item.delete()
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        if not order.items.exists():
            order.table.status = TableInfo.Status.AVAILABLE
            order.table.save()

        return Response(OrderSerializer(order).data)

# bill generation

def generate_bill_number(cafe, table_no):
    """Bill numbers are unique per cafe, not globally."""
    today = timezone.now()
    count_today = Bill.objects.filter(cafe=cafe, created_at__date=today.date()).count() + 1
    return f"{table_no:02d}{count_today:04d}{today.day:02d}{today.month:02d}"


class SettleOrderAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(
            Order, pk=order_id, status=Order.Status.ACTIVE, table__cafe=request.user.cafe
        )
        payment_method = request.data.get('payment_method')
        note = request.data.get('note', '').strip()

        if payment_method not in Bill.PaymentMethod.values:
            return Response({'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)
        if not order.items.exists():
            return Response({'error': 'Cannot settle an empty order'}, status=status.HTTP_400_BAD_REQUEST)

        order_items = order.items.select_related('variant__item')
        total = sum(oi.subtotal for oi in order_items)

        parts = []
        for oi in order_items:
            name = oi.variant.item.name
            size = oi.variant.get_size_display()
            label = name if size == 'Default' else f'{name} ({size})'
            parts.append(f'{label} x{oi.quantity}')

        bill = Bill.objects.create(
            cafe=request.user.cafe,
            bill_number=generate_bill_number(request.user.cafe, order.table.table_no),
            order=order, table=order.table,
            total_amount=total, payment_method=payment_method,
            items_summary=', '.join(parts), note=note,
        )

        order.status = Order.Status.CLOSED
        order.save()
        order.table.status = TableInfo.Status.AVAILABLE
        order.table.save()

        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class BillListAPI(generics.ListAPIView):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(cafe=self.request.user.cafe).select_related('table').order_by('-created_at')


class BillDetailAPI(generics.RetrieveAPIView):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(cafe=self.request.user.cafe)


# reports

class SalesReportAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cafe = request.user.cafe
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        agg = lambda qs: qs.aggregate(total=Sum('total_amount'), count=Count('id'))

        return Response({
            'daily': agg(Bill.objects.filter(cafe=cafe, created_at__date=today)),
            'weekly': agg(Bill.objects.filter(cafe=cafe, created_at__date__gte=week_start)),
            'monthly': agg(Bill.objects.filter(cafe=cafe, created_at__date__gte=month_start)),
        })