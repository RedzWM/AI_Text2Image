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
print("Your public IP and region info:")
print(requests.get("https://ipinfo.io/json").json())


# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# === Generate image from Gemini-native ===
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
                file_path = "gemini_native_image.png"
                with open(file_path, "wb") as f:
                    f.write(part.inline_data.data)
                return file_path
    except Exception as e:
        print("Gemini Error:", e)
    return None

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Gemini-native!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("✨ Đang tạo ảnh từ Gemini...")
    image_path = await generate_image(prompt)
    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini-native ảnh")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
