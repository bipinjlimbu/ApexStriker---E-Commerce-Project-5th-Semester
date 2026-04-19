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
    # 1. Get the encoded data from the URL
    encoded_data = request.GET.get('data')
    if not encoded_data:
        return redirect('payment_failed')

    # 2. Decode the response
    decoded_bytes = base64.b64decode(encoded_data)
    decoded_data = json.loads(decoded_bytes.decode('utf-8'))
    
    # 3. VERIFY WITH ESEWA (Backend handshake)
    # We must check if the status is 'COMPLETE' via their API
    product_code = "EPAYTEST"
    transaction_uuid = decoded_data['transaction_uuid']
    total_amount = decoded_data['total_amount']
    
    # Verification URL for Sandbox
    verify_url = f"https://uat.esewa.com.np/api/epay/transaction/status/?product_code={product_code}&total_amount={total_amount}&transaction_uuid={transaction_uuid}"
    
    response = requests.get(verify_url)
    verification_status = response.json()

    if verification_status.get('status') == "COMPLETE":
        # --- START ORDER CREATION ---
        customer = request.user.customer # Adjust based on your Auth model
        cart_items = Cart.objects.filter(customer=customer)
        
        # 1. Create the Main Order
        order = Order.objects.create(
            customer=customer,
            total_amount=float(total_amount.replace(',', '')), # Remove commas if any
            transaction_id=transaction_uuid,
            status=Order.Status.PAID,
            shipping_address=customer.shipping_address # Ensure this field exists in Customer
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
        
        # 3. CLEAR THE CART
        cart_items.delete()
        
        messages.success(request, "Deployment Confirmed. Gear is being prepared.")
        return render(request, 'store/payment_confirmed.html', {'order': order})

    else:
        messages.error(request, "Verification Failed. Protocol Aborted.")
        return redirect('payment_failed')