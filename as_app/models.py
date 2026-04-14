from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        VENDOR = 'vendor', 'Vendor'
        CUSTOMER = 'customer', 'Customer'
        
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    profile_picture = models.ImageField(upload_to='images/user/', blank=True, null=True)
    auth_token = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username},{self.role}"
    
class Vendor(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='vendor_profile')
    shop_name = models.CharField(max_length=255)
    pan_number = models.CharField(max_length=50)
    id_proof = models.FileField(upload_to='images/id_proof/')
    bank_account_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    requested_on = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.shop_name} ({self.user.username})"
    
class Customer(models.Model):
    class Position(models.TextChoices):
        ATTACKER = 'attacker', 'Attacker'
        MIDFIELDER = 'midfielder', 'Midfielder'
        DEFENDER = 'defender', 'Defender'
        GOALKEEPER = 'goalkeeper', 'Goalkeeper'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    position = models.CharField(max_length=20,null=True,blank=True, choices=Position.choices)
    
    def __str__(self):
        return f"{self.user.username} ({self.position})"
    
class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='images/brands/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    class Position(models.TextChoices):
        ATTACKER = 'attacker', 'Attacker'
        MIDFIELDER = 'midfielder', 'Midfielder'
        DEFENDER = 'defender', 'Defender'
        GOALKEEPER = 'goalkeeper', 'Goalkeeper'
        
    class Category(models.TextChoices):
        KITS = 'kits', 'Jersey & Kits'
        BOOTS = 'boots', 'Football Boots'
        ACCESSORIES = 'accessories', 'Accessories (Socks, Guards)'
        EQUIPMENT = 'equipment', 'Training Equipment (Balls, Cones)'
        SUPPLEMENTS = 'supplements', 'Health & Supplements'
        
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    position = models.CharField(max_length=20, choices=Position.choices, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_new(self):
        return self.created_at >= timezone.now() - timedelta(days=7)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/products/')
    is_primary = models.BooleanField(default=False)
    
    def get_primary(self):
        return self.product.images.filter(is_primary=True).first()
    
class Wishlist(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Cart(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    class Status(models.TextChoices):
        PAID = 'paid', 'Paid (Held by Admin)'
        SHIPPED = 'shipped', 'Shipped'
        COMPLETED = 'completed', 'Delivered & Received'
        CANCELLED = 'cancelled', 'Cancelled'

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    transaction_id = models.CharField(max_length=100, help_text="eSewa/Khalti Ref ID")
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

class Disbursement(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount after commission")
    admin_commission = models.DecimalField(max_digits=12, decimal_places=2)
    is_transferred = models.BooleanField(default=False)
    bank_ref_no = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    class Reason(models.TextChoices):
        FRAUD = 'fraud', 'Fraudulent Activity'
        QUALITY = 'quality', 'Poor Item Quality'
        FAKE_ID = 'fake_id', 'Fake Identity/Shop'
        OTHER = 'other', 'Other'

    reporter = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reports_sent')
    reported_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)