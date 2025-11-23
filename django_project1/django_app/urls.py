from django.urls import path
from django_app import views
urlpatterns = [

    ##TODO AUTHENTICATION##
    path('api/login/', views.login_view),
    path('api/logout/', views.logout_view),

    ##TODO USERS (Только суперадмин)##
    path('api/users/get/', views.users_get),
    path('api/users/post/', views.users_post),
    path('api/users/put/<int:user_id>/', views.users_put),
    path('api/users/delete/<int:user_id>/', views.users_delete),
    path('api/users/get/<int:user_id>/', views.single_user_get),

    ##TODO PRODUCTS##
    path('api/products/get/', views.products_get),
    path('api/products/get/<int:product_id>/', views.single_product_get),
    path('api/products/post/', views.products_post),
    path('api/products/put/<int:product_id>/', views.products_put),
    path('api/products/delete/<int:product_id>/', views.products_delete),

    ##TODO CARTS##
    path('api/carts/', views.get_carts),
    path('api/cart/', views.get_user_cart),
    path('api/carts/add/<int:product_id>/', views.add_to_cart),
]    