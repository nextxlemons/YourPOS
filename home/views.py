from functools import wraps

from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from home.models import Cafe, TableInfo, MenuCategory, MenuItem, MenuVariant, Order, OrderItem, Bill


# helping functions

def _has_cafe(user):
    """True if this user is authenticated AND linked to a Cafe."""
    return hasattr(user, 'cafe')


def cafe_login_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _has_cafe(request.user):
            logout(request)
            messages.error(request, "Your account isn't linked to a café. Please log in with a café account.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def bill_payload(order):
    """Plain helper — not a view, no decorator needed."""
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


def generate_bill_number(cafe, table_no):
    """
    Format: TT CCCC DD MM  (per café)
    TT = table number (01-20+)
    CCCC = daily counter for this café (0001-1000+)
    DD/MM = day/month
    e.g. Table 5, 12th bill today for this café, on 4th July -> 05001204 07
    """
    today = timezone.now()
    count_today = Bill.objects.filter(cafe=cafe, created_at__date=today.date()).count() + 1
    return f"{table_no:02d}{count_today:04d}{today.day:02d}{today.month:02d}"


# sign log auth

def signup_view(request):
    if request.user.is_authenticated and _has_cafe(request.user):
        return redirect('home')

    if request.method == 'POST':
        cafe_name = request.POST.get('cafe_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not all([cafe_name, username, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'signup.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        Cafe.objects.create(owner=user, name=cafe_name)

        login(request, user)
        messages.success(request, f"Welcome, {cafe_name}! Your account is ready.")
        return redirect('home')

    return render(request, 'signup.html')


def login_view(request):
    if request.user.is_authenticated and _has_cafe(request.user):
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not _has_cafe(user):
                messages.error(request, "This account isn't linked to a café. Please contact support.")
                return render(request, 'login.html')
            login(request, user)
            messages.success(request, f"Welcome back, {user.cafe.name}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# home dashboard
@cafe_login_required
def home(request):
    cafe = request.user.cafe
    today = timezone.now().date()

    today_bills = Bill.objects.filter(cafe=cafe, created_at__date=today)
    today_stats = today_bills.aggregate(total=Sum("total_amount"), count=Count("id"))

    recent_bill = Bill.objects.filter(cafe=cafe).select_related("table").order_by("-created_at").first()

    occupied_tables = TableInfo.objects.filter(cafe=cafe, status=TableInfo.Status.OCCUPIED).order_by("table_no")
    total_tables = TableInfo.objects.filter(cafe=cafe).count()

    return render(request, "home.html", {
        "today_total": today_stats["total"] or 0,
        "today_count": today_stats["count"] or 0,
        "recent_bill": recent_bill,
        "occupied_tables": occupied_tables,
        "occupied_count": occupied_tables.count(),
        "total_tables": total_tables,
    })


# table and orders

@cafe_login_required
def orders(request):
    cafe = request.user.cafe

    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'add_table':
            last_table = TableInfo.objects.filter(cafe=cafe).order_by('-table_no').first()
            next_table_no = (last_table.table_no + 1) if last_table else 1

            TableInfo.objects.create(cafe=cafe, table_no=next_table_no)
            messages.success(request, f"Table {next_table_no} added successfully.")
            return redirect('orders')

    data = TableInfo.objects.filter(cafe=cafe).order_by('table_no')
    return render(request, 'orders.html', {'items': data})


@cafe_login_required
def createorders(request, table_id):
    table = get_object_or_404(TableInfo, pk=table_id, cafe=request.user.cafe)
    order, created = Order.objects.get_or_create(table=table, status=Order.Status.ACTIVE)

    categories = MenuCategory.objects.filter(cafe=request.user.cafe, is_active=True)
    return render(request, "createorders.html", {
        "table": table, "order": order, "categories": categories,
    })


@cafe_login_required
def category_items(request, category_id):
    category = get_object_or_404(MenuCategory, pk=category_id, cafe=request.user.cafe)
    items = MenuItem.objects.filter(category=category, is_active=True).prefetch_related("variants")
    data = [{
        "id": item.id,
        "name": item.name,
        "variants": [
            {"id": v.id, "size_display": v.get_size_display(), "price": str(v.price)}
            for v in item.variants.all()
        ]
    } for item in items]
    return JsonResponse(data, safe=False)


@cafe_login_required
@require_POST
def add_order_item(request, order_id):
    order = get_object_or_404(
        Order, pk=order_id, status=Order.Status.ACTIVE, table__cafe=request.user.cafe
    )
    variant = get_object_or_404(
        MenuVariant, pk=request.POST.get("variant_id"), item__category__cafe=request.user.cafe
    )

    order_item, created = OrderItem.objects.get_or_create(order=order, variant=variant, defaults={"quantity": 1})
    if not created:
        order_item.quantity += 1
        order_item.save()

    if order.table.status != TableInfo.Status.OCCUPIED:
        order.table.status = TableInfo.Status.OCCUPIED
        order.table.save()

    return JsonResponse(bill_payload(order))


@cafe_login_required
@require_POST
def update_order_item(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, order__table__cafe=request.user.cafe)
    action = request.POST.get("action")
    order = item.order

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

    if not order.items.exists():
        order.table.status = TableInfo.Status.AVAILABLE
        order.table.save()

    return JsonResponse(bill_payload(order))


@cafe_login_required
@require_POST
def settle_order(request, order_id):
    cafe = request.user.cafe
    order = get_object_or_404(
        Order, pk=order_id, status=Order.Status.ACTIVE, table__cafe=cafe
    )
    payment_method = request.POST.get("payment_method")
    note = request.POST.get("note", "").strip()

    if payment_method not in Bill.PaymentMethod.values:
        return JsonResponse({"error": "Invalid payment method"}, status=400)
    if not order.items.exists():
        return JsonResponse({"error": "Cannot settle an empty order"}, status=400)

    order_items = order.items.select_related("variant__item")
    total = sum(oi.subtotal for oi in order_items)

    parts = []
    for oi in order_items:
        name = oi.variant.item.name
        size = oi.variant.get_size_display()
        label = name if size == "Default" else f"{name} ({size})"
        parts.append(f"{label} x{oi.quantity}")
    items_summary = ", ".join(parts)

    bill = Bill.objects.create(
        cafe=cafe,
        bill_number=generate_bill_number(cafe, order.table.table_no),
        order=order, table=order.table,
        total_amount=total, payment_method=payment_method,
        items_summary=items_summary,
        note=note,
    )
    messages.success(
        request,
        f"Order settled successfully. Table Number: {bill.table.table_no}, Bill Number: {bill.bill_number}"
    )

    order.status = Order.Status.CLOSED
    order.save()
    order.table.status = TableInfo.Status.AVAILABLE
    order.table.save()

    return JsonResponse({"success": True, "bill_number": bill.bill_number, "redirect": "/orders"})


# reports

@cafe_login_required
def orderhistory(request):
    bills = Bill.objects.filter(cafe=request.user.cafe).select_related("table").order_by("-created_at")
    return render(request, "orderhistory.html", {"bills": bills})


@cafe_login_required
def settings(request):
    return render(request, "settings.html")


@cafe_login_required
def salesreport(request):
    cafe = request.user.cafe
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    agg = lambda qs: qs.aggregate(total=Sum("total_amount"), count=Count("id"))
    return render(request, "salesreport.html", {
        "daily": agg(Bill.objects.filter(cafe=cafe, created_at__date=today)),
        "weekly": agg(Bill.objects.filter(cafe=cafe, created_at__date__gte=week_start)),
        "monthly": agg(Bill.objects.filter(cafe=cafe, created_at__date__gte=month_start)),
    })


# menu and items
@cafe_login_required
def managecategories(request):
    cafe = request.user.cafe

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'add_category':
            name = request.POST.get('name')
            MenuCategory.objects.create(cafe=cafe, name=name)
            messages.success(request, f"Category '{name}' added successfully.")

        elif action == 'rename_category':
            old_name = request.POST.get('old_name')
            new_name = request.POST.get('new_name')
            MenuCategory.objects.filter(cafe=cafe, name=old_name).update(name=new_name)
            messages.success(request, f"Category renamed from '{old_name}' to '{new_name}'.")

        elif action == 'delete_category':
            category_name = request.POST.get('category_name')
            MenuCategory.objects.filter(cafe=cafe, name=category_name).delete()
            messages.success(request, f"Category '{category_name}' deleted successfully.")

        return redirect('managecategories')

    data = MenuCategory.objects.filter(cafe=cafe).order_by('name')
    return render(request, 'managecategories.html', {'items': data})


@cafe_login_required
def manageitems(request):
    cafe = request.user.cafe

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == "delete_item":
            name = request.POST.get('item_name')
            MenuItem.objects.filter(name=name, category__cafe=cafe).delete()
            messages.success(request, f"Item '{name}' deleted successfully.")
            return redirect('manageitems')

    data = (
        MenuItem.objects.filter(category__cafe=cafe)
        .select_related('category')
        .prefetch_related('variants')
        .order_by('category_id')
    )
    return render(request, 'manageitems.html', {'items': data})


@cafe_login_required
def additems(request):
    cafe = request.user.cafe
    categories = MenuCategory.objects.filter(cafe=cafe, is_active=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        has_variants = request.POST.get('has_variants') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        category = get_object_or_404(MenuCategory, id=category_id, cafe=cafe)

        item = MenuItem.objects.create(name=name, category=category, is_active=is_active)

        if has_variants:
            variant_price_s = request.POST.get('variant_price_s')
            variant_price_l = request.POST.get('variant_price_l')

            if variant_price_s:
                MenuVariant.objects.create(item=item, size="S", price=variant_price_s)
            if variant_price_l:
                MenuVariant.objects.create(item=item, size="L", price=variant_price_l)
        else:
            variant_price_d = request.POST.get('variant_price_d')
            MenuVariant.objects.create(item=item, size="D", price=variant_price_d)

        messages.success(request, f"Item '{name}' added successfully.")
        return redirect('manageitems')

    return render(request, 'additems.html', {'categories': categories})


@cafe_login_required
def edititem(request, pk):
    cafe = request.user.cafe
    item = get_object_or_404(MenuItem.objects.prefetch_related('variants'), pk=pk, category__cafe=cafe)
    categories = MenuCategory.objects.filter(cafe=cafe, is_active=True)

    if request.method == 'POST':
        item.name = request.POST.get('name', '').strip()
        item.category = get_object_or_404(MenuCategory, id=request.POST.get('category'), cafe=cafe)
        item.is_active = request.POST.get('is_active') == 'on'
        has_variants = request.POST.get('has_variants') == 'on'
        item.save()

        item.variants.all().delete()
        if has_variants:
            price_s = request.POST.get('variant_price_s')
            price_l = request.POST.get('variant_price_l')
            MenuVariant.objects.update_or_create(item=item, size='S', defaults={'price': price_s}) if price_s else None
            MenuVariant.objects.update_or_create(item=item, size='L', defaults={'price': price_l}) if price_l else None
        else:
            price_d = request.POST.get('variant_price_d')
            MenuVariant.objects.update_or_create(item=item, size='D', defaults={'price': price_d}) if price_d else None

        messages.success(request, f"Item '{item.name}' updated successfully.")
        return redirect('manageitems')

    variants = {v.size: v.price for v in item.variants.all()}
    has_variants = item.variants.filter(size__in=['S', 'L']).exists()

    return render(request, 'edititem.html', {
        'item': item,
        'categories': categories,
        'variants': variants,
        'has_variants': has_variants,
    })