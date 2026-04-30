from xml.dom import ValidationErr

from django.db import models

# table to show status of all tables 

#all tables in cafe 
class TableInfo(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "A", "Available"
        OCCUPIED = "O", "Occupied"

    table_no = models.IntegerField(primary_key=True)
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    def __str__(self):
        return f"Table {self.table_no}"
  

# table menu of category
class MenuCategory(models.Model):
    name = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# menu of cafe,
class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.PROTECT,
        related_name="items"
    )
    name = models.CharField(max_length=150, unique=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("category", "name")
    def __str__(self):
        return f"{self.name} - {self.category.name}"


#  size of items Large or Small
class MenuVariant(models.Model):
    class Size(models.TextChoices):
        SMALL = "S", "Small"
        LARGE = "L", "Large"

    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    size= models.CharField(max_length=5, choices=Size.choices)
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

# # order where order 
# class OrderItem(models.Model):
#     class ServeStatus(models.TextChoices):
#         PENDING = "pending", "Pending"
#         SERVED = "served", "Served"

#     order = models.ForeignKey(
#         Order,
#         on_delete=models.CASCADE,
#         related_name="items"
#     )
#     menu_item = models.ForeignKey(
#         MenuItem,
#         on_delete=models.PROTECT
#     )
#     variant = models.ForeignKey(
#         MenuVariant,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL
#     )
#     quantity = models.PositiveIntegerField(default=1)
#     unit_price = models.DecimalField(max_digits=8, decimal_places=2)
#     notes = models.CharField(max_length=200, blank=True)
#     serve_status = models.CharField(
#         max_length=20,
#         choices=ServeStatus.choices,
#         default=ServeStatus.PENDING
#     )

#     def clean(self):
#         if self.variant and self.variant.item != self.menu_item:
#             raise ValidationErr("Selected variant does not belong to selected menu item.")

#     @property
#     def total_price(self):
#         return self.quantity * self.unit_price

#     def __str__(self):
#         return f"{self.quantity} x {self.menu_item.name}"

# # order bill 
# class Bill(models.Model):
#     order = models.OneToOneField(
#         Order,
#         on_delete=models.PROTECT,
#         related_name="bill"
#     )
#     bill_number = models.CharField(max_length=20, unique=True)
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)
#     cgst = models.DecimalField(max_digits=8, decimal_places=2, default=0)
#     sgst = models.DecimalField(max_digits=8, decimal_places=2, default=0)
#     discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
#     total = models.DecimalField(max_digits=10, decimal_places=2)
#     billed_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Bill {self.bill_number}"

# # how payment is done 
# class Payment(models.Model):
#     class Mode(models.TextChoices):
#         CASH = "cash", "Cash"
#         CARD = "card", "Card"
#         UPI = "upi", "UPI"

#     bill = models.ForeignKey(
#         Bill,
#         on_delete=models.PROTECT,
#         related_name="payments"
#     )
#     mode = models.CharField(max_length=10, choices=Mode.choices)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     reference = models.CharField(max_length=100, blank=True)
#     paid_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.mode} - ₹{self.amount}"