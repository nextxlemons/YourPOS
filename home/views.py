from django.shortcuts import redirect, render, get_object_or_404
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from home.models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill


# Create your views here.
def index(request):
    return render(request,'index.html')

def home(request):
    return render(request, 'home.html')

def orders(request):
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'add_table':
            table_no = request.POST.get('table_no')
            table_add = TableInfo(table_no=table_no)
            table_add.save()
            return redirect('orders')

    data = TableInfo.objects.all().order_by('table_no')
    # context = {'items': data} for context passing
    return render(request, 'orders.html', {'items': data})


def createorders(request, table_id):
    table = get_object_or_404(TableInfo, pk=table_id)
    order, created = Order.objects.get_or_create(table=table, status=Order.Status.ACTIVE)
    if created:
        table.status = TableInfo.Status.OCCUPIED
        table.save()
    categories = MenuCategory.objects.filter(is_active=True)
    return render(request, "createorders.html", {
        "table": table, "order": order, "categories": categories,
    })


def category_items(request, category_id):
    items = MenuItem.objects.filter(category_id=category_id, is_active=True).prefetch_related("variants")
    data = [{
        "id": item.id,
        "name": item.name,
        "variants": [
            {"id": v.id, "size_display": v.get_size_display(), "price": str(v.price)}
            for v in item.variants.all()
        ]
    } for item in items]
    return JsonResponse(data, safe=False)


def bill_payload(order):
    items, total = [], 0
    for oi in order.items.select_related("variant__item").all():
        subtotal = float(oi.subtotal)
        total += subtotal
        items.append({
            "id": oi.id,
            "name": oi.variant.item.name,
            "size": oi.variant.get_size_display(),
            "quantity": oi.quantity,
            "subtotal": subtotal,
        })
    return {"items": items, "total": round(total, 2)}


@require_POST
def add_order_item(request, order_id):
    order = get_object_or_404(Order, pk=order_id, status=Order.Status.ACTIVE)
    variant = get_object_or_404(MenuVariant, pk=request.POST.get("variant_id"))

    order_item, created = OrderItem.objects.get_or_create(order=order, variant=variant, defaults={"quantity": 1})
    if not created:
        order_item.quantity += 1
        order_item.save()

    return JsonResponse(bill_payload(order))


@require_POST
def update_order_item(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id)
    action = request.POST.get("action")

    if action == "inc":
        item.quantity += 1
        item.save()
    elif action == "dec":
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
    elif action == "remove":
        item.delete()

    return JsonResponse(bill_payload(item.order))



@require_POST
def settle_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, status=Order.Status.ACTIVE)
    payment_method = request.POST.get("payment_method")

    if payment_method not in Bill.PaymentMethod.values:
        return JsonResponse({"error": "Invalid payment method"}, status=400)
    if not order.items.exists():
        return JsonResponse({"error": "Cannot settle an empty order"}, status=400)

    total = sum(oi.subtotal for oi in order.items.all())
    bill = Bill.objects.create(
        bill_number=generate_bill_number(order.table.table_no),
        order=order, table=order.table,
        total_amount=total, payment_method=payment_method,
    )

    order.status = Order.Status.CLOSED
    order.save()
    order.table.status = TableInfo.Status.AVAILABLE
    order.table.save()


    return JsonResponse({"success": True, "bill_number": bill.bill_number, "redirect": "/orders"})


def generate_bill_number(table_no):
    """
    Format: TT CCCC DD MM
    TT = table number (01-20+), CCCC = daily counter (0001-1000+), DD/MM = day/month
    e.g. Table 5, 12th bill today, on 4th July -> 05001204 07  (05-0012-04-07)
    """
    today = timezone.now()
    count_today = Bill.objects.filter(created_at__date=today.date()).count() + 1
    return f"{table_no:02d}{count_today:04d}{today.day:02d}{today.month:02d}"

def orderhistory(request):
    bills = Bill.objects.select_related("table").order_by("-created_at")
    return render(request, "orderhistory.html", {"bills": bills})


def salesreport(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    agg = lambda qs: qs.aggregate(total=Sum("total_amount"), count=Count("id"))
    return render(request, "salesreport.html", {
        "daily": agg(Bill.objects.filter(created_at__date=today)),
        "weekly": agg(Bill.objects.filter(created_at__date__gte=week_start)),
        "monthly": agg(Bill.objects.filter(created_at__date__gte=month_start)),
    })



def reports(request):
    return render(request, 'reports.html')


def managecategories(request):
    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'add_category':
            name = request.POST.get('name')
            MenuCategory.objects.create(name=name)

        elif action == 'rename_category':
            old_name = request.POST.get('old_name')
            new_name = request.POST.get('new_name')
            MenuCategory.objects.filter(name=old_name).update(name=new_name)

        elif action == 'delete_category':
            category_name = request.POST.get('category_name')
            MenuCategory.objects.filter(name=category_name).delete()

        return redirect('managecategories')

    data = MenuCategory.objects.all().order_by('name')
    return render(request, 'managecategories.html', {'items': data})


def manageitems(request):

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == "delete_item":
            name = request.POST.get('item_name')
            MenuItem.objects.filter(name=name).delete()

    data = MenuItem.objects.select_related('category').prefetch_related('variants').order_by('category_id')
    return render(request, 'manageitems.html', {'items': data})


def additems(request):
    categories = MenuCategory.objects.filter(is_active=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        has_variants = request.POST.get('has_variants') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        category = MenuCategory.objects.get(id=category_id)

        item = MenuItem.objects.create(name=name, category=category, is_active=is_active)

        if has_variants:
            variant_price_s= request.POST.get('variant_price_s')
            variant_price_l= request.POST.get('variant_price_l')

            if variant_price_s:
                MenuVariant.objects.create(item=item,size="S",price=variant_price_s)

            if variant_price_l:
                MenuVariant.objects.create(item=item,size="L",price=variant_price_l)
            
        else:
            variant_price_d = request.POST.get('variant_price_d')
            MenuVariant.objects.create(item=item,size="D",price=variant_price_d)

        return redirect('manageitems')

    return render(request, 'additems.html', {'categories': categories})


def edititem(request, pk):
    item = MenuItem.objects.prefetch_related('variants').get(pk=pk)
    categories = MenuCategory.objects.filter(is_active=True)

    if request.method == 'POST':
        item.name = request.POST.get('name', '').strip()
        item.category = MenuCategory.objects.get(id=request.POST.get('category'))
        item.is_active = request.POST.get('is_active') == 'on'
        has_variants = request.POST.get('has_variants') == 'on'
        item.save()

        item.variants.all().delete()  # remove old variants if switched
        if has_variants: # if has variants, create S and L variants
            price_s = request.POST.get('variant_price_s')
            price_l = request.POST.get('variant_price_l')
            MenuVariant.objects.update_or_create(item=item, size='S', defaults={'price': price_s}) if price_s else None
            MenuVariant.objects.update_or_create(item=item, size='L', defaults={'price': price_l}) if price_l else None
        else: # if no variants, create D variant
            price_d = request.POST.get('variant_price_d')
            MenuVariant.objects.update_or_create(item=item, size='D', defaults={'price': price_d}) if price_d else None

        return redirect('manageitems')

    # pass prices to template
    variants = {v.size: v.price for v in item.variants.all()}
    has_variants = item.variants.filter(size__in=['S', 'L']).exists()  # explicit flag

    return render(request, 'edititem.html', {
        'item': item,
        'categories': categories,
        'variants': variants,
        'has_variants': has_variants,
    })
