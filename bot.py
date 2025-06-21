import os
import openai
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình API
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# === Hàm tạo ảnh từ OpenAI DALL·E ===
async def generate_dalle(prompt):
    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        try:
            print("OpenAI (DALL·E) Error:", e.response.json())
        except:
            print("OpenAI (DALL·E) Error:", e)
        return None

# === Hàm tạo ảnh từ Google Gemini ===
async def generate_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(
                response_mime_type=["image"]
            )
        )
        for part in response.parts:
            if hasattr(part, "inline_data") and part.inline_data.data:
                image_data = part.inline_data.data
                file_path = "gemini_image.png"
                with open(file_path, "wb") as f:
                    f.write(image_data)
                return file_path
        return None
    except Exception as e:
        print("Gemini Error:", e)
        return None

# === Hàm xử lý prompt từ người dùng ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("⚠️ Prompt không được để trống.")
        return

    await update.message.reply_text("🧠 Đang tạo ảnh từ OpenAI (DALL·E)...")
    dalle_url = await generate_dalle(prompt)
    if dalle_url:
        await update.message.reply_photo(photo=dalle_url, caption="🟢 OpenAI (DALL·E v3)")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh từ OpenAI.")

    await update.message.reply_text("✨ Tiếp tục tạo ảnh từ Google Gemini...")
    gemini_path = await generate_gemini(prompt)
    if gemini_path:
        with open(gemini_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Google Gemini")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh từ Gemini.")

# === Hàm khởi động bot (/start) ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi mình prompt mô tả hình ảnh bạn muốn tạo!")

# === Chạy bot với polling ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
