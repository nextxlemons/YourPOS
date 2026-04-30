from django.shortcuts import redirect, render
from django.db import models

from home.models import TableInfo, MenuCategory, MenuItem, MenuVariant, Order

# Create your views here.
def index(request):
    return render(request,'index.html')

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

        if has_variants:
            item = MenuItem.objects.create(
                name=name, category=category,
                base_price=0, is_active=is_active
            )
            variant_price_s= request.POST.get('variant_price_s')
            variant_price_l= request.POST.get('variant_price_l')

            if variant_price_s:
                MenuVariant.objects.create(item=item,size="S",price=variant_price_s)

            if variant_price_l:
                MenuVariant.objects.create(item=item,size="L",price=variant_price_l)
            
        else:
            base_price = request.POST.get('base_price')
            item = MenuItem.objects.create(
                name=name, category=category,
                base_price=base_price, is_active=is_active
            )

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

        if has_variants:
            item.base_price = 0
            item.save()
            price_s = request.POST.get('variant_price_s')
            price_l = request.POST.get('variant_price_l')
            MenuVariant.objects.update_or_create(item=item, size='S', defaults={'price': price_s}) if price_s else None
            MenuVariant.objects.update_or_create(item=item, size='L', defaults={'price': price_l}) if price_l else None
        else:
            item.base_price = request.POST.get('base_price')
            item.save()
            item.variants.all().delete()  # remove old variants if switched to flat price

        return redirect('manageitems')

    # pass existing variant prices to template
    variants = {v.size: v.price for v in item.variants.all()}
    return render(request, 'edititem.html', {
        'item': item,
        'categories': categories,
        'variants': variants,
    })