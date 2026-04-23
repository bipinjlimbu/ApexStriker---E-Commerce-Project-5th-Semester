from django.urls import path
from .views.auth_view import register_view, login_view, logout_view
from .views.main_view import home_view, verify_email_view, password_reset_view, password_reset_confirm_view
from .views.profile_view import profile_view, edit_profile_view, resend_verification_email, delete_profile_view
from .views.brand_view import brands_view, add_brand_view, approve_brand_view, edit_brand_view, delete_brand_view
from .views.product_view import add_product_view, marketplace_view, edit_product_view, delete_product_view, single_product_view, wishlist_toggle_view
from .views.order_view import cart_view, update_cart_quantity, dispatch_item_view, receive_item_view, mark_order_as_pickup
from .views.payment_view import initiate_esewa_payment, payment_success, payment_failed
from .views.dashboard import admin_dashboard_view, approve_vendor_view, reject_vendor_view, vendor_dashboard_view, customer_dashboard_view, wishlist_remove_view, cancel_order_view, remove_order_view

urlpatterns = [
    path('', home_view, name='home_page'),
    path('brands/', brands_view, name='brands_page'),
    path('register/', register_view, name='register_page'),
    path('verify/<str:token>/', verify_email_view, name='verify_email'),
    path('password-reset/', password_reset_view, name='password_reset_page'),
    path('password-reset/<str:token>/', password_reset_confirm_view, name='password_reset_confirm_page'),
    path('login/', login_view, name='login_page'),
    path('logout/', logout_view, name='logout_page'),
    path('profile/<int:user_id>/', profile_view, name='profile_page'),
    path('profile/edit/<int:user_id>/', edit_profile_view, name='edit_profile_page'),
    path('profile/resend_verification/<int:user_id>/', resend_verification_email, name='resend_verification_email'),
    path('profile/delete/<int:user_id>/', delete_profile_view, name='delete_profile_page'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('approve_vendor/<int:vendor_id>/', approve_vendor_view, name='approve_vendor'),
    path('reject_vendor/<int:vendor_id>/', reject_vendor_view, name='reject_vendor'),
    path('dashboard/vendor/', vendor_dashboard_view, name='vendor_dashboard'),
    path('dashboard/customer/', customer_dashboard_view, name='customer_dashboard'),
    path('brands/add/', add_brand_view, name='add_brand'),
    path('brands/edit/<int:brand_id>/', edit_brand_view, name='edit_brand'),
    path('brands/approve/<int:brand_id>/', approve_brand_view, name='approve_brand'),
    path('brands/delete/<int:brand_id>/', delete_brand_view, name='delete_brand'),
    path('products/add/', add_product_view, name='add_product'),
    path('marketplace/', marketplace_view, name='marketplace_page'),
    path('products/edit/<int:product_id>/', edit_product_view, name='edit_product'),
    path('products/delete/<int:product_id>/', delete_product_view, name='delete_product'),
    path('products/<int:product_id>/', single_product_view, name='single_product_page'),
    path('wishlist/toggle/<int:product_id>/', wishlist_toggle_view, name='wishlist_toggle'),
    path('wishlist/remove/<int:item_id>/', wishlist_remove_view, name='wishlist_remove'),
    path('cart/', cart_view, name='cart_page'),
    path('cart/update-quantity/', update_cart_quantity, name='update_cart_quantity'),
    path('payment/initiate/', initiate_esewa_payment, name='initiate_esewa_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/failed/', payment_failed, name='payment_failed'),
    path('orders/cancel/<int:order_id>/', cancel_order_view, name='cancel_order'),
    path('orders/remove/<int:order_id>/', remove_order_view, name='remove_order'),
    path('orders/dispatch/<int:item_id>/', dispatch_item_view, name='dispatch_item'),
    path('orders/receive/<int:item_id>/', receive_item_view, name='receive_item'),
    path('orders/pickup/<int:order_id>/', mark_order_as_pickup, name='mark_order_as_pickup'),
]
