from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:pk>/', views.delete_product, name='delete_product'),

   path('login/', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),

  path('userlogin/', views.userlogin, name='userlogin'),
  path('register/', views.register, name='register'),
 path('cart/', views.cart_view, name='cart'),
  path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
  path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
  path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
  path('checkout/', views.checkout, name='checkout'),
  path('invoice/', views.invoice, name='invoice'),
  path('invoice/download/', views.download_invoice, name='download_invoice'),
  path('logout/', views.user_logout, name='logout'),

]
