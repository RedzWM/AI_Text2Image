import os
import openai
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# Load biến môi trường từ Railway (hoặc .env local)
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình client OpenAI
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)

# === HÀM TẠO ẢNH TỪ DALL·E (OpenAI) ===
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
        print("OpenAI (DALL·E) Error:", e)
        return None

# === HÀM TẠO ẢNH TỪ GEMINI ===
async def generate_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            contents=prompt,
            generation_config={
                "response_mime_type": ["image"]
            }
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

# === XỬ LÝ PROMPT ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🧠 Đang tạo ảnh từ OpenAI và Gemini...")

    dalle_url = await generate_dalle(prompt)
    gemini_path = await generate_gemini(prompt)

    if dalle_url:
        await update.message.reply_photo(photo=dalle_url, caption="🟢 OpenAI (DALL·E v3)")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh từ OpenAI.")

    if gemini_path:
        with open(gemini_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Google Gemini")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh từ Gemini.")

# === BẮT ĐẦU BOT ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi mình prompt mô tả hình ảnh bạn muốn tạo!")

# === CHẠY ỨNG DỤNG ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
