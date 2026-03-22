from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        VENDOR = 'vendor', 'Vendor'
        CUSTOMER = 'customer', 'Customer'
        
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    profile_picture = models.ImageField(upload_to='images/user/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username},{self.role}"
    
class Vendor(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='vendor_profile')
    shop_name = models.CharField(max_length=255)
    shop_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    pan_number = models.CharField(max_length=50)
    id_proof = models.FileField(upload_to='images/id_proof/')
    bank_account_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    
    def __str__(self):
        return f"{self.shop_name} ({self.user.username})"
    
class Customer(models.Model):
    class Position(models.TextChoices):
        ATTACKER = 'attacker', 'Attacker'
        MIDFIELDER = 'midfielder', 'Midfielder'
        DEFENDER = 'defender', 'Defender'
        GOALKEEPER = 'goalkeeper', 'Goalkeeper'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    shipping_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    position = models.CharField(max_length=20,null=True,blank=True, choices=Position.choices)
    
    def __str__(self):
        return f"{self.user.username} ({self.position})"