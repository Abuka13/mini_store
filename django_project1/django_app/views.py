from django.shortcuts import render
from .models import User
from . import models
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test

def is_super_admin(user):
    return user.role == 'super_admin'

def is_admin(user):
    return user.role == 'admin'
VALID_ROLES = ["superadmin", "admin", "user"]


##TODO USERS##
@csrf_exempt
@user_passes_test(is_super_admin)
def users_get(request):
    if request.method == 'GET':
        users = User.objects.all().values('id', 'name', 'last_name', 'role', 'password')
        return JsonResponse(list(users), safe=False)
@csrf_exempt
@user_passes_test(is_super_admin)
def single_user_get(request,user_id):
    if request.method == "GET":
        user = User.objects.get(user_id = user_id)
        return JsonResponse(user)        
@csrf_exempt
@user_passes_test(is_super_admin)
def users_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data['role'] not in VALID_ROLES:
                return JsonResponse(
                    {"error": f"Invalid role '{data['role']}'. Allowed: {VALID_ROLES}"},
                    status=400
                )
        user.role = data['role']
        user = User.objects.create(name=data['name'], last_name=data['last_name'], password=data['password'], role=data.get('role'))
        return JsonResponse({'id': user.id, 'name': user.name, 'last_name': user.last_name, 'role': user.role}, status=201)
@csrf_exempt
@user_passes_test(is_super_admin)
def users_put(request, user_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        if data['role'] not in VALID_ROLES:
                return JsonResponse(
                    {"error": f"Invalid role '{data['role']}'. Allowed: {VALID_ROLES}"},
                    status=400
                )
        user.role = data['role']
        user = models.User.objects.get(id=user_id)
        user.name = data.get('name', user.name)
        user.last_name = data.get('last_name', user.last_name)
        user.password = data.get('password', user.password)
        
        user.save()
        return JsonResponse({'id': user.id, 'name': user.name, 'last_name': user.last_name})
@csrf_exempt
@user_passes_test(is_super_admin)
def users_delete(request, user_id):
    if request.method == 'DELETE':
        user = models.User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'message': 'User deleted'})   



##TODO PRODUCTS##
@csrf_exempt
def products_get(request):
    if request.method == 'GET':
        products = Product.objects.all().values('id', 'name', 'description', 'category', 'price')
        return JsonResponse(list(products), safe=False)
@csrf_exempt
def single_product_get(request,product_id):
    if request.method == "GET":
        product = Product.objects.get(product_id = product_id)
        return JsonResponse(product)
@csrf_exempt
@user_passes_test(is_admin)
def products_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product = Product.objects.create(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            price=data['price'],
        )
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'price': str(product.price)
        }, status=201)
@csrf_exempt
@user_passes_test(is_admin)
def products_put(request, product_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        product = models.Product.objects.get(id=product_id)
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.category = data.get('category', product.category)
        product.price = data.get('price', product.price)
        
        product.save()
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'price': str(product.price),
        })               
    
@csrf_exempt
@user_passes_test(is_admin)
def products_delete(request, product_id):
    if request.method == 'DELETE':
        product = models.Product.objects.get(id=product_id)
        product.delete()
        return JsonResponse({'message': 'Product deleted'})



##TODO CARTS AND CART ITEMS##

@csrf_exempt
def get_user_cart(request, user_id):
    if request.method == 'GET':
        cart = Cart.objects.filter(user_id=user_id)
        if not cart.exists():
            return JsonResponse({'error': 'Cart not found'}, status=404)
        items = CartItem.objects.filter(cart=cart).select_related('product')
        data = []
        for item in items:
            data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.product.price),
            }) 

@csrf_exempt
def add_to_cart(request, user_id, product_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            product = Product.objects.get(id=product_id)

            cart, created = Cart.objects.get_or_create(user_id=user_id)
            data = json.loads(request.body) 
            quantity = data.get('quantity', 1)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()

            return JsonResponse({'message': 'Product added to cart'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404) 
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)                   
 