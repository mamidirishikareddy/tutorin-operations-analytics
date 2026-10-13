# app/notifier.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# Twilio Config
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize Twilio client
client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_sms(to, message):
    """
    Send SMS to parent
    """
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to
        )
        print(f"✅ SMS sent to {to}")
        return True
    except Exception as e:
        print(f"❌ SMS send error to {to}: {e}")
        return False

def send_whatsapp(to, message):
    """
    Send WhatsApp message to parent
    """
    try:
        client.messages.create(
            body=message,
            from_='whatsapp:' + TWILIO_PHONE,
            to='whatsapp:' + to
        )
        print(f"✅ WhatsApp message sent to {to}")
        return True
    except Exception as e:
        print(f"❌ WhatsApp send error to {to}: {e}")
        return False
