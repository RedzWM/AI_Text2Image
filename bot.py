import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

from google.api_core.client_options import ClientOptions
from google.ai.generativelanguage_v1beta import (
    Content, Part, GenerateContentRequest, GenerationConfig,
    GenerativeServiceClient
)
from PIL import Image
from io import BytesIO

# === Load biến môi trường ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Cấu hình Gemini client ===
client = GenerativeServiceClient(
    client_options=ClientOptions(api_key=GEMINI_API_KEY)
)

# === Hàm tạo ảnh với Gemini ===
async def generate_gemini_image(prompt):
    try:
        request = GenerateContentRequest(
            model="models/gemini-2.0-pro-preview-image",
            contents=[
                Content(role="user", parts=[Part(text=prompt)])
            ],
            generation_config=GenerationConfig(
                response_mime_type=["image"]
            )
        )
        response = client.generate_content(request=request)

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data.data:
                    image_data = part.inline_data.data
                    file_path = "gemini_image_output.png"
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    return file_path
    except Exception as e:
        print("Gemini Error:", e)
    return None

# === Xử lý prompt từ người dùng Telegram ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("⚠️ Prompt không được để trống.")
        return

    await update.message.reply_text("🧠 Đang tạo ảnh với Gemini...")

    image_path = await generate_gemini_image(prompt)
    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini 2.0")
    else:
        await update.message.reply_text("❌ Không thể tạo ảnh từ Gemini.")

# === Lệnh /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh với Gemini API mới nhất!")

# === Khởi chạy bot ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
