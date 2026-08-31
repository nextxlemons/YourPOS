from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps


def _has_cafe(user):
    return hasattr(user, 'cafe')


def cafe_login_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _has_cafe(request.user):
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Your account isn't linked to a café. Please log in with a café account.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------- Auth pages (just render forms — JS calls the API) ----------

def signup_view(request):
    if request.user.is_authenticated and _has_cafe(request.user):
        return redirect('home')
    return render(request, 'signup.html')


def login_view(request):
    if request.user.is_authenticated and _has_cafe(request.user):
        return redirect('home')
    return render(request, 'login.html')


def logout_view(request):
    # kept as a plain redirect target; actual logout happens via API + JS,
    # but this exists as a fallback / non-JS safety net
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')


# ---------- App pages (shells only — JS fetches data from the API) ----------

@cafe_login_required
def home(request):
    return render(request, 'home.html')


@cafe_login_required
def orders(request):
    return render(request, 'orders.html')


@cafe_login_required
def createorders(request, table_id):
    return render(request, 'createorders.html', {'table_id': table_id})


@cafe_login_required
def orderhistory(request):
    return render(request, 'orderhistory.html')


@cafe_login_required
def profile(request):
    return render(request,'profile.html')

@cafe_login_required
def settings(request):
    return render(request, 'settings.html')


@cafe_login_required
def salesreport(request):
    return render(request, 'salesreport.html')


@cafe_login_required
def managecategories(request):
    return render(request, 'managecategories.html')


@cafe_login_required
def manageitems(request):
    return render(request, 'manageitems.html')


@cafe_login_required
def additems(request):
    return render(request, 'additems.html')



@cafe_login_required
def edititem(request, pk):
    return render(request, 'edititem.html', {'item_id': pk})
