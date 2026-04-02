import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ---------------- GMAIL CONFIG (SAFE) ----------------
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ---------------- SEND EMAIL ----------------
def send_price_alert(receiver_email, product, store, old_price, new_price):

    # ❌ safety check
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Email credentials not set")
        return

    if not receiver_email:
        print("❌ No receiver email")
        return

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

        # ---------------- SMTP ----------------
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()

        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, receiver_email, msg.as_string())

        server.quit()

        print(f"📧 Email sent to {receiver_email}")

    except Exception as e:
        print("❌ Email sending failed:", e)