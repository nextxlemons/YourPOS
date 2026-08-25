from xml.dom import ValidationErr

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

# table to show status of all tables 

# table for user of cafe

class Cafe(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cafe')
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
#all tables in cafe 
class TableInfo(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "A", "Available"
        OCCUPIED = "O", "Occupied"

    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='tables')
    table_no = models.IntegerField()
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    class Meta:
        unique_together = ('cafe', 'table_no')

    def __str__(self):
        return f"Table {self.table_no}"

    @classmethod
    def next_table_no(cls, cafe):
        last = cls.objects.filter(cafe=cafe).order_by('-table_no').first()
        return (last.table_no + 1) if last else 1
    
# table menu of category
class MenuCategory(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('cafe', 'name')

    def __str__(self):
        return self.name

    
# menu of cafe,
class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.name} - {self.category.name}"


#  size of items Large or Small and default price of items
class MenuVariant(models.Model):
    class Size(models.TextChoices):
        DEFAULT = "D", "Default"
        SMALL = "S", "Small"
        LARGE = "L", "Large"
        

    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    size= models.CharField(max_length=10, choices=Size.choices,default=Size.DEFAULT)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("item", "size")

    def __str__(self):
        return f"{self.item.name} - {self.get_size_display()}"
  

# table for order status 
class Order(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "A", "Active"
        CLOSED = "C", "Closed"

    table = models.ForeignKey(
        TableInfo,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - Table {self.table.table_no}"
    
    @property
    def total(self):
        return sum(oi.subtotal for oi in self.items.all())
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(MenuVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("order", "variant")

    @property
    def subtotal(self):
        return self.variant.price * self.quantity

    def __str__(self):
        return f"{self.variant} x {self.quantity}"
    


class Bill(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        UPI = "UPI", "UPI"

    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='bills')

    bill_number = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="bill")
    table = models.ForeignKey(TableInfo, on_delete=models.PROTECT)
    items_summary = models.CharField(max_length=1000, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    note = models.CharField(max_length=1000, blank=True)
    
    payment_method = models.CharField(max_length=5, choices=PaymentMethod.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_number

    class Meta:
            unique_together = ('cafe', 'bill_number')  # bill numbers reset per café, not globally unique anymore