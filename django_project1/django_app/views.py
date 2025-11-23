from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Product
from .models import Cart
from .models import CartItem
from . import models
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test, login_required
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

def is_super_admin(user):
    return user.is_authenticated and user.is_superuser
def is_admin(user):
    return user.is_authenticated and user.is_staff
def is_user(user):
    return user.is_authenticated and not user.is_staff and not user.is_superuser

def get_user_role(user):
    if user.is_superuser:
        return "superadmin"
    elif user.is_staff:
        return "admin"
    else:
        return "user"
VALID_ROLES = ["superadmin", "admin", "user"]


##TODO AUTHENTICATION ##
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'role': get_user_role(user),
                'user_id': user.id,
                'token': token.key,
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        logout(request)
        return JsonResponse({'message': 'Logout successful'})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


from functools import wraps


def token_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Authentication required'}, status=401)

        token_key = auth_header.replace('Token ', '')
        try:
            token = Token.objects.get(key=token_key)
            request.user = token.user
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper

##TODO USERS##
@csrf_exempt
@token_required
@user_passes_test(is_super_admin)
def users_get(request):
    if request.method == 'GET':
        users = User.objects.all()
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': get_user_role(user)
            })
        return JsonResponse(users_list, safe=False)
@csrf_exempt
@token_required
@user_passes_test(is_super_admin)
def single_user_get(request, user_id):
    if request.method == "GET":
        try:
            user = User.objects.get(id=user_id)
            return JsonResponse({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": get_user_role(user)
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


@csrf_exempt
@token_required
@user_passes_test(is_super_admin)
def users_put(request, user_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=user_id)

            if 'role' in data:
                role = data['role']
                if role not in VALID_ROLES:
                    return JsonResponse(
                        {"error": f"Invalid role '{role}'. Allowed: {VALID_ROLES}"},
                        status=400
                    )
                user.is_superuser = (role == 'superadmin')
                user.is_staff = (role in ['admin', 'superadmin'])

            user.username = data.get('username', user.username)
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.email = data.get('email', user.email)

            if 'password' in data:
                user.set_password(data['password'])

            user.save()
            return JsonResponse({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': get_user_role(user)
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@token_required
@user_passes_test(is_super_admin)
def users_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        role = data.get('role', 'user')
        
        if role not in VALID_ROLES:
            return JsonResponse(
                {"error": f"Invalid role '{role}'. Allowed: {VALID_ROLES}"},
                status=400
            )
        
        is_superuser = (role == 'superadmin')
        is_staff = (role == 'admin')
        
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', ''),
            is_superuser=is_superuser,
            is_staff=is_staff
        )
        
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': get_user_role(user)
        }, status=201)  
@csrf_exempt
@token_required
@user_passes_test(is_super_admin)
def users_delete(request, user_id):
    if request.method == 'DELETE':
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return JsonResponse({'message': 'User deleted'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)       



##TODO PRODUCTS##
@csrf_exempt
@token_required
def products_get(request):
    if request.method == 'GET':
        products = Product.objects.all().values('id', 'name', 'description', 'category', 'price')
        return JsonResponse(list(products), safe=False)
@csrf_exempt
@token_required
def single_product_get(request,product_id):
    if request.method == "GET":
        try:
            product = Product.objects.get(id = product_id)
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': product.category,
                'price': str(product.price)
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)    
@csrf_exempt
@token_required
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
@token_required
@user_passes_test(is_admin)
def products_put(request, product_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            product = Product.objects.get(id=product_id)
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
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)              
    
@csrf_exempt
@token_required
@user_passes_test(is_admin)
def products_delete(request, product_id):
    if request.method == 'DELETE':
        try:
            product = models.Product.objects.get(id=product_id)
            product.delete()
            return JsonResponse({'message': 'Product deleted'})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)


##TODO CARTS AND CART ITEMS##
@csrf_exempt
@token_required
@user_passes_test(is_admin)
def get_carts(request, user_id):
    if request.method == 'GET':
        carts = Cart.objects.all()
        return JsonResponse(list(carts), safe=False)


@csrf_exempt
@token_required
def get_user_cart(request):
    if request.method == 'GET':
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return JsonResponse({'items' : [], 'total': '0'})
        items = CartItem.objects.filter(cart=cart).select_related('product')
        data = []
        total = 0
        for item in items:
            item_total = item.quantity * item.product.price
            total += item_total
            data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.product.price),
            })
        return JsonResponse({
            'items': data,
            'total': str(total)})


@csrf_exempt
@token_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            data = json.loads(request.body) if request.body else {}
            quantity = data.get('quantity', 1)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return JsonResponse({
                'message': 'Product added to cart',
                'quantity': cart_item.quantity
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)                  
 