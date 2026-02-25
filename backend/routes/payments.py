# /backend/routers/payments.py
from fastapi import APIRouter, Depends, Request, HTTPException
from backend.payments.stripe_provider import StripeProvider
from backend.payments.paypal_provider import PayPalProvider

router = APIRouter()

def get_payment_provider(provider: str):
    if provider == "paypal":
        return PayPalProvider()
    return StripeProvider() # Default

class BuyRequest(BaseModel):
    package_id: str
    provider: str  # 'stripe' or 'paypal'

@router.post("/checkout")
async def create_checkout(request: BuyRequest, current_user = Depends(get_current_user)):
    # 1. Select the correct driver
    driver = get_payment_provider(request.provider)
    
    # 2. Run the logic (Frontend doesn't know the difference)
    return driver.create_checkout_session(request.package_id, str(current_user.id))

@router.post("/webhook/{provider}")
async def payment_webhook(provider: str, request: Request):
    """
    Receives webhooks from Stripe or PayPal
    """
    driver = get_payment_provider(provider)
    
    # Get the raw JSON body
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Verify and Process
    # Note: For strict security, you should also verify headers here 
    # (Stripe-Signature or Paypal-Transmission-Sig)
    result = driver.verify_webhook(payload)

    if result and result['status'] == 'paid':
        # TODO: Update your Database here!
        # await user_service.add_credits(result['user_id'], result['credits'])
        print(f"SUCCESS: Added {result['credits']} credits to User {result['user_id']}")
        return {"status": "success"}

    return {"status": "ignored"}