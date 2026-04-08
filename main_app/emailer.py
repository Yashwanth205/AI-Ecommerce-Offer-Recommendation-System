import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = (
    os.environ.get("EMAIL_ADDRESS")
    or os.environ.get("SMTP_USERNAME")
    or os.environ.get("EMAIL_USER")
)
EMAIL_PASSWORD = (
    os.environ.get("EMAIL_PASSWORD")
    or os.environ.get("SMTP_PASSWORD")
    or os.environ.get("EMAIL_APP_PASSWORD")
)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_TIMEOUT = int(os.environ.get("SMTP_TIMEOUT", "10"))
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "false").lower() == "true"
EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "smtp").lower()
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL")


def _build_subject_and_body(product, store, old_price, new_price):
    subject = f"DealAI Alert: Price change detected for {product}"
    body = f"""
Hello,

Your watched product has a price update.

Product: {product}
Store: {store}

Old Price: {old_price}
New Price: {new_price}

Visit DealAI to check the best deal now.
"""
    return subject, body


def _send_via_resend(receiver_email, subject, body):
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        print("Resend config missing (RESEND_API_KEY/RESEND_FROM_EMAIL)")
        return False

    try:
        payload = {
            "from": RESEND_FROM_EMAIL,
            "to": [receiver_email],
            "subject": subject,
            "text": body.strip(),
        }
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=10,
        )
        if response.status_code in (200, 201):
            print("Email sent via Resend API")
            return True

        print(f"Resend send failed: {response.status_code} {response.text}")
        return False
    except Exception as e:
        print("Resend send exception:", e)
        return False


def send_price_alert(receiver_email, product, store, old_price, new_price):
    subject, body = _build_subject_and_body(product, store, old_price, new_price)

    if EMAIL_PROVIDER == "resend":
        return _send_via_resend(receiver_email, subject, body)

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Email credentials are missing (EMAIL_ADDRESS/EMAIL_PASSWORD)")
        # Try HTTPS-based provider when SMTP credentials are absent.
        return _send_via_resend(receiver_email, subject, body)

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
            server.ehlo()
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, receiver_email, msg.as_string())
        server.quit()

        print("📧 Email sent to:", receiver_email)
        return True

    except Exception as e:
        print("❌ Email sending failed:", e)
        # SMTP blocked/unreachable on some platforms; fallback to HTTPS provider if configured.
        return _send_via_resend(receiver_email, subject, body)