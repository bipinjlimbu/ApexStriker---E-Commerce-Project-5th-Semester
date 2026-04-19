from django.conf import settings
from django.shortcuts import render, redirect
from ..models import Cart, Order, OrderItem
from django.contrib import messages
import requests
import json
import hmac
import hashlib
import base64
import uuid

def initiate_esewa_payment(request):
    if request.method == "POST":
        total_amount = request.POST.get('total_amount')
        
        # eSewa v2 is extremely strict: '100.0' and '100' create different hashes.
        # We ensure it matches the exact string that will be in the HTML form.
        try:
            total_val = float(total_amount)
            if total_val.is_integer():
                total_amount = str(int(total_val))
            else:
                total_amount = "{:.2f}".format(total_val) # Standardize decimal if exists
        except:
            return redirect('cart')

        transaction_uuid = str(uuid.uuid4())
        product_code = "EPAYTEST"
        
        # CORRECT SANDBOX SECRET KEY
        secret_key = "8gBm/:&EnhH.1/q" 
        
        # THE SIGNATURE FORMULA (No spaces after commas)
        # Sequence must be: total_amount,transaction_uuid,product_code
        data_to_sign = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        # Generate HMAC-SHA256
        secret_key_bytes = secret_key.encode('utf-8')
        data_bytes = data_to_sign.encode('utf-8')
        hmac_sha256 = hmac.new(secret_key_bytes, data_bytes, hashlib.sha256).digest()
        
        # Base64 Encode
        signature = base64.b64encode(hmac_sha256).decode('utf-8')
        
        context = {
            'amount': total_amount,
            'transaction_uuid': transaction_uuid,
            'product_code': product_code,
            'signature': signature,
            'esewa_url': "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
            'success_url': "http://127.0.0.1:8000/payment/success/",
            'failure_url': "http://127.0.0.1:8000/payment/failed/",
        }
        
        return render(request, 'main/esewa_redirect_page.html', context)
    
    return redirect('cart')

def payment_success(request):
    encoded_data = request.GET.get('data')
    if not encoded_data:
        return redirect('payment_failed')

    decoded_bytes = base64.b64decode(encoded_data)
    decoded_data = json.loads(decoded_bytes.decode('utf-8'))
    
    product_code = "EPAYTEST"
    transaction_uuid = decoded_data['transaction_uuid']
    total_amount = decoded_data['total_amount']
    
    # FIXED URL: uat.esewa.com.np is dead. Use rc-epay.
    verify_url = "https://rc-epay.esewa.com.np/api/epay/transaction/status/"
    params = {
        'product_code': product_code,
        'total_amount': total_amount,
        'transaction_uuid': transaction_uuid
    }
    
    try:
        # Single request with timeout and params
        response = requests.get(verify_url, params=params, timeout=10)
        response.raise_for_status()
        verification_status = response.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        messages.error(request, "Communication failure with eSewa. Check DNS/Internet.")
        return redirect('payment_failed')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('payment_failed')

    if verification_status.get('status') == "COMPLETE":
        # --- DB SAVING LOGIC (AS PER YOUR ORIGINAL) ---
        customer = request.user.customer
        cart_items = Cart.objects.filter(customer=customer)
        
        # 1. Create Main Order
        order = Order.objects.create(
            customer=customer,
            total_amount=float(total_amount.replace(',', '')),
            transaction_id=transaction_uuid,
            status=Order.Status.PAID,
            shipping_address=customer.shipping_address
        )
        
        # 2. Move items from Cart to OrderItem
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                vendor=item.product.vendor,
                price_at_purchase=item.product.price,
                quantity=item.quantity
            )
        
        # 3. Clear Cart
        cart_items.delete()
        
        return render(request, 'main/payment_confirmed_page.html', {'order': order})

    else:
        messages.error(request, "Verification Failed. Protocol Aborted.")
        return redirect('payment_failed')
    
def payment_failed(request):
    messages.error(request, "Payment Failed or Cancelled. Please try again.")
    return render(request, 'main/payment_failed_page.html')