import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_TIMEOUT = int(os.environ.get("SMTP_TIMEOUT", "10"))


def send_price_alert(receiver_email, product, store, old_price, new_price):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Email credentials are missing (EMAIL_ADDRESS/EMAIL_PASSWORD)")
        return False

    try:
        subject = f"🔥 DealAI Alert: Price change detected for {product}"
        body = f"""
Hello 👋,

Your watched product has a price update!

Product: {product}
Store: {store}

Old Price: ₹{old_price}
New Price: ₹{new_price}

👉 Visit DealAI to check the best deal now.

Happy Saving 💰
— DealAI Smart Offer Recommendation System
"""
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

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
        return False