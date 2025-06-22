import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from google import genai
from google.genai import types

import requests
try:
    ip_info = requests.get("https://ipinfo.io/json").json()
    print(f"🔍 Railway Server IP: {ip_info.get('ip')} — {ip_info.get('country')}")
except Exception as e:
    print("❌ IP check failed:", e)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Initialize Google AI Client
client = genai.Client(api_key=GEMINI_API_KEY)

# === Image generation ===
async def generate_imagen(prompt: str):
    try:
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=4)
        )
        paths = []
        for i, generated_image in enumerate(response.generated_images):
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            path = f"imagen_generated_{i}.png"
            image.save(path)
            paths.append(path)
        return paths
    except Exception as e:
        print("Imagen Error:", e)
        return []

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Imagen 3.0!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("🎨 Đang tạo ảnh...")
    image_paths = await generate_imagen(prompt)

    if image_paths:
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                await update.message.reply_photo(photo=img)
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Imagen 3.0.")

# === Main bot startup ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )
