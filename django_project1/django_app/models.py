from django.db import models

class User(models.Model):
    ROLE_CHOICES = (
        ('superadmin', 'супер админ'),
        ('admin', 'админ'),
        ('user', 'пользователь'),
    )
    
    name = models.CharField(max_length=150)  
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    password = models.CharField(max_length=128)
    class Meta:
        db_table = 'user'
class Product (models.Model):
    CATEGORY_CHOICES = (
        ('clothes', 'Одежда'),
        ('sport', 'Спорт'),
        ('home', 'Дом'),
        ('electronics', 'Электроника'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='clothes'
    )
    class Meta:
        db_table = 'product'    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True) 
    class Meta:
        db_table = 'cart'       
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        db_table = 'cartitem'
    
