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

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Debug IP info (optional for Render)
try:
    ip_info = requests.get("https://ipinfo.io/json").json()
    print(f"🌐 Public IP: {ip_info.get('ip')} — Country: {ip_info.get('country')}")
except Exception as e:
    print("⚠️ Cannot retrieve IP info:", e)

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# === Image generation ===
async def generate_image(prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        paths = []
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                file_path = "gemini_generated_image.png"
                with open(file_path, "wb") as f:
                    f.write(part.inline_data.data)
                paths.append(file_path)
        return paths
    except Exception as e:
        print("Gemini Error:", e)
        return []

# === Telegram handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Gemini 2.0 Flash!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("🎨 Đang tạo ảnh...")
    image_paths = await generate_image(prompt)

    if image_paths:
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                await update.message.reply_photo(photo=img)
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Gemini 2.0.")

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
