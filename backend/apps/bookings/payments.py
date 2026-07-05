"""
Razorpay integration for refundable booking deposits.

DEV MODE (default, no keys configured): every function returns fake-but-realistic IDs and
auto-approves, so you can test the entire deposit → refund/forfeit pipeline without a real
Razorpay account. The moment RAZORPAY_KEY_ID/SECRET are set in .env, these functions switch
to making real API calls — no other code needs to change.

Get real test keys (free) at https://dashboard.razorpay.com/app/keys once you're ready to
test against the real sandbox.
"""
import uuid

from django.conf import settings


def _is_dev_mode() -> bool:
    return not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def create_order(amount_rupees, receipt: str) -> dict:
    """Creates a Razorpay order for the deposit amount. Returns a dict with at least
    'id', 'amount' (in paise), 'currency', and 'is_stub' (tells the frontend whether to
    show a real Razorpay checkout or a dev 'Simulate Payment' button)."""
    amount_paise = int(float(amount_rupees) * 100)

    if _is_dev_mode():
        return {
            "id": f"order_dev_{uuid.uuid4().hex[:14]}",
            "amount": amount_paise,
            "currency": "INR",
            "is_stub": True,
        }

    import razorpay  # local import so the package is only required once real keys are configured

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1,
    })
    order["is_stub"] = False
    return order


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verifies the checkout was genuine (not forged client-side). Dev-mode orders always
    verify true so local testing doesn't need a real checkout flow at all."""
    if _is_dev_mode() or order_id.startswith("order_dev_"):
        return True

    import razorpay

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def verify_payment_amount(order_id: str, payment_id: str, expected_amount_rupees) -> bool:
    """
    Signature verification alone only proves the payment response wasn't tampered with
    client-side — it does NOT confirm the amount actually captured matches what we expected.
    Without this check, a technically-valid-signature payment for ₹1 could be used to
    satisfy a ₹500 deposit requirement if an attacker found any way to initiate a smaller
    real payment against a manipulated order. This fetches the actual captured payment from
    Razorpay's servers and compares it against our own records — never trusting a client-
    supplied amount.
    Dev-mode always passes since there's no real payment to check.
    """
    if _is_dev_mode() or order_id.startswith("order_dev_") or payment_id.startswith("pay_dev_"):
        return True

    import razorpay

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.payment.fetch(payment_id)
    expected_paise = int(float(expected_amount_rupees) * 100)
    return (
        payment.get("order_id") == order_id
        and payment.get("status") == "captured"
        and int(payment.get("amount", 0)) == expected_paise
    )


def refund_payment(payment_id: str, amount_rupees) -> dict:
    """Issues a refund. Dev-mode payment IDs (pay_dev_...) get a fake refund ID instantly."""
    amount_paise = int(float(amount_rupees) * 100)

    if _is_dev_mode() or payment_id.startswith("pay_dev_"):
        return {"id": f"rfnd_dev_{uuid.uuid4().hex[:14]}", "is_stub": True}

    import razorpay

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    refund = client.payment.refund(payment_id, {"amount": amount_paise})
    refund["is_stub"] = False
    return refund


# Flat deposit fee per bed type (in rupees). Simple for now — could later scale with hospital
# tier or bed cost; kept as a flat table so it's trivial to tune during testing.
DEPOSIT_AMOUNTS = {
    "general": 100,
    "icu": 500,
    "ventilator": 1000,
    "maternity": 300,
    "emergency": 500,
}


def get_deposit_amount(bed_type: str):
    return DEPOSIT_AMOUNTS.get(bed_type, 100)
