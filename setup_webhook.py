import os
import requests
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
response = requests.post(url, json={"url": WEBHOOK_URL})

print("Webhook set:", response.json())
