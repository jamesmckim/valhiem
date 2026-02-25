# backend/routers/payments.py
from fastapi import APIRouter, Depends
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