# backend/payments/paypal_provider.py
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest
from .driver import PaymentProvider
from config.packages import CREDIT_PACKAGES
import os

class PayPalProvider(PaymentProvider):
    def __init__(self):
        client_id = os.getenv("PAYPAL_CLIENT_ID")
        client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        # Switch to LiveEnvironment for production
        self.environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
        self.client = PayPalHttpClient(self.environment)
        self.domain = os.getenv("DOMAIN_URL")

    def create_checkout_session(self, package_id, user_id):
        package = CREDIT_PACKAGES.get(package_id)
        
        request = OrdersCreateRequest()
        request.prefer('return=representation')
        request.request_body({
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": package_id, # Helps us identify the item later
                "custom_id": user_id,       # Helps us identify the user
                "amount": {
                    "currency_code": "USD",
                    "value": str(package['price_usd'])
                }
            }],
            "application_context": {
                "return_url": self.domain + "/dashboard?success=true",
                "cancel_url": self.domain + "/dashboard?canceled=true"
            }
        })

        try:
            response = self.client.execute(request)
            # Find the approval URL in the response links
            for link in response.result.links:
                if link.rel == "approve":
                    return {"url": link.href}
        except Exception as e:
            print(e)
            raise Exception("PayPal creation failed")