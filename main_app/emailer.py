import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")


def send_price_alert(receiver_email, product, store, old_price, new_price):
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

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, receiver_email, msg.as_string())
        server.quit()

        print("📧 Email sent to:", receiver_email)

    except Exception as e:
        print("❌ Email sending failed:", e)