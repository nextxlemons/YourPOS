from django.db import models

# Create your models here.

# table to show status of all tables 
class table(models.Model):
    TABLE_STATUS = {
        "A": "Available",
        "O": "Occupied",
    }
    table_no = models.CharField(max_length=3, primary_key=True)
    status = models.CharField(max_length=10, choices=TABLE_STATUS)

    def __str__(self):
        return self.table_no
