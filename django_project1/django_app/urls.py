from django.urls import path
from django_app import views
urlpatterns = [

    ##TODO USERS##
    path('users/get', views.users_get),
    path('users/post', views.users_post),
    path('users/put/<int:user_id>', views.users_put),
    path('users/delete/<int:user_id>', views.users_delete),
    path('users/get/<int:user_id>', views.single_user_get),

    ##TODO PRODUCTS##
    path('products/get', views.products_get),
    path('products/get/<int:product_id>', views.single_product_get),
    path('products/post', views.products_post),
    path('products/put/<int:product_id>', views.products_put),
    path('products/delete/<int:product_id>', views.products_delete),

    ##TODO CARTS##
    path('carts/get/<int:user_id>', views.carts_get),
    path('carts/add/<int:user_id>/<int:product_id>', views.add_to_cart),
]    