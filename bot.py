import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from PIL import Image
from io import BytesIO

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

async def generate_image(prompt: str):
    try:
        response = model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(response_mime_type=["image"])
        )
        for part in response.parts:
            if part.inline_data and part.inline_data.data:
                file_path = "gemini_image.png"
                with open(file_path, "wb") as f:
                    f.write(part.inline_data.data)
                return file_path
    except Exception as e:
        print("Gemini Error:", e)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Gemini 2.5!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("✨ Đang tạo ảnh bằng Gemini...")
    image_path = await generate_image(prompt)
    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini 2.5 Flash")
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Gemini.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )
