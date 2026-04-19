from django.conf import settings
from django.shortcuts import render, redirect
from ..models import Cart
import hmac
import hashlib
import base64
import uuid

def initiate_esewa_payment(request):
    if request.method == "POST":
        customer = request.user.customer_profile
        total_amount = request.POST.get('total_amount')
        
        # 1. Create a Unique Transaction UUID
        # We use this to track the payment before the Order is actually created
        transaction_uuid = str(uuid.uuid4())
        
        # 2. eSewa Credentials (Use Test Credentials for now)
        # In production, move these to settings.py
        product_code = "EPAYTEST"
        secret_key = "8g8M89dgBdb9" # Official eSewa Test Secret Key
        
        # 3. Generate Signature
        # Formula: total_amount,transaction_uuid,product_code
        data_to_sign = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        secret_key_bytes = secret_key.encode('utf-8')
        data_bytes = data_to_sign.encode('utf-8')
        
        hmac_sha256 = hmac.new(secret_key_bytes, data_bytes, hashlib.sha256).digest()
        hash_in_base64 = base64.b64encode(hmac_sha256).decode('utf-8')
        
        # 4. Prepare Context for the Gateway Redirect Page
        context = {
            'amount': total_amount,
            'transaction_uuid': transaction_uuid,
            'product_code': product_code,
            'signature': hash_in_base64,
            'esewa_url': "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
            'success_url': "http://127.0.0.1:8000/payment-success/", # Update to your domain
            'failure_url': "http://127.0.0.1:8000/payment-failed/",
        }
        
        return render(request, 'store/esewa_redirect.html', context)
    
    return redirect('cart')