import base64
from ninja import Router

from helper.helper import load_public_key, verify_signature
from webhook.schemas import WebhookPayload

# Create your views here.

webhook = Router(tags=["Webhook"])

@webhook.post("/transaction", auth=None)
def transaction_status_webhook(request, payload:WebhookPayload):
    # signature_b64 = request.headers.get('X-Request-Signature')
    # if not signature_b64:
    #     return webhook.api.create_response(request, {"details": "Unauthorized request"}, status=400)
    # try:
    #     signature = base64.b64decode(signature_b64)
    # except Exception as e:
    #     return webhook.api.create_response(request, {"details": "Unauthorized request"}, status=400)

    # raw_body = request.body

    # # Load Paybis' public key
    # public_key = load_public_key()

    # if not verify_signature(public_key, signature, raw_body):
    #     return webhook.api.create_response(request, {"details": "Not a verified user"}, status=400)

    # Log the event and transaction status
    event = payload.event
    transaction_status = payload.data.transaction.status

    print(f"Received event: {event}")
    print(f"Transaction status: {transaction_status}")

    # You can implement your business logic here based on the event and status
    if transaction_status == "completed":
        print("Transaction completed successfully!")
    elif transaction_status == "cancelled":
        print("Transaction was cancelled by the client.")
    elif transaction_status == "rejected":
        reject_reason = payload.data.transaction.rejectReason
        print(f"Transaction rejected: {reject_reason}")
    return webhook.api.create_response(request, payload, status=200)
