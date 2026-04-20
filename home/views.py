from django.shortcuts import render
from django.db import models

from home.models import table

# Create your views here.
def index(request):
    return render(request,'index.html')

def orders(request):
    data = table.objects.all()
    return render(request, 'orders.html', {'items': data})



def reports(request):
    return render(request, 'reports.html')