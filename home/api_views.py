from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill
from .serializers import (
    TableInfoSerializer, MenuCategorySerializer, MenuItemSerializer,
    OrderSerializer, BillSerializer,
)
from .views import generate_bill_number  # reuse


class TableListAPI(generics.ListAPIView):
    queryset = TableInfo.objects.all().order_by('table_no')
    serializer_class = TableInfoSerializer
    permission_classes = [AllowAny]  # later 


class MenuCategoryListAPI(generics.ListAPIView):
    queryset = MenuCategory.objects.filter(is_active=True)
    serializer_class = MenuCategorySerializer
    permission_classes = [AllowAny]


class MenuItemListAPI(generics.ListAPIView):
    queryset = MenuItem.objects.filter(is_active=True).select_related('category').prefetch_related('variants')
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


class OrderDetailAPI(generics.RetrieveAPIView):
    queryset = Order.objects.select_related('table').prefetch_related('items__variant__item')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


class BillListAPI(generics.ListAPIView):
    queryset = Bill.objects.select_related('table').order_by('-created_at')
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]



class AddOrderItemAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, status=Order.Status.ACTIVE)
        variant_id = request.data.get('variant_id')
        variant = get_object_or_404(MenuVariant, pk=variant_id)

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


class SettleOrderAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, status=Order.Status.ACTIVE)
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
            bill_number=generate_bill_number(order.table.table_no),
            order=order, table=order.table,
            total_amount=total, payment_method=payment_method,
            items_summary=', '.join(parts), note=note,
        )

        order.status = Order.Status.CLOSED
        order.save()
        order.table.status = TableInfo.Status.AVAILABLE
        order.table.save()

        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class SalesReportAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        agg = lambda qs: qs.aggregate(total=Sum('total_amount'), count=Count('id'))
        return Response({
            'daily': agg(Bill.objects.filter(created_at__date=today)),
            'weekly': agg(Bill.objects.filter(created_at__date__gte=week_start)),
            'monthly': agg(Bill.objects.filter(created_at__date__gte=month_start)),
        })