from django.contrib import admin
from django_app.models import Product
from django_app.models import Cart
from django_app.models import CartItem
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
# Register your models here.
