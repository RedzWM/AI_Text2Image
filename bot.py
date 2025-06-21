import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# === Load biến môi trường ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Cấu hình Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
client = genai.Client()

# === Hàm tạo ảnh từ Gemini-native ===
async def generate_gemini_image(prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                file_path = "gemini_native_image.png"
                with open(file_path, "wb") as f:
                    f.write(image_data)
                return file_path
        return None
    except Exception as e:
        print("Gemini-native Error:", e)
        return None

# === Xử lý prompt từ người dùng Telegram ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("⚠️ Prompt không được để trống.")
        return

    await update.message.reply_text("✨ Đang tạo ảnh từ Gemini-native...")

    image_path = await generate_gemini_image(prompt)
    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini 2.0 Image")
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Gemini.")

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Gemini!")

# === Khởi chạy bot ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
