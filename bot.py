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

# Load env
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Init Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Image generation
async def generate_image(prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                path = "gemini_2_flash_output.png"
                with open(path, "wb") as f:
                    f.write(part.inline_data.data)
                return path
    except Exception as e:
        print("Gemini Error:", e)
    return None

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔹 Gửi prompt để tạo ảnh bằng Gemini 2.0 Flash!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("🌀 Đang tạo ảnh từ Gemini 2.0...")
    image_path = await generate_image(prompt)
    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🖼 Gemini 2.0 Flash")
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Gemini.")

# Start bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )
