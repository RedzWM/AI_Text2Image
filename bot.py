import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

from google.api_core.client_options import ClientOptions
from google.ai.generativelanguage_v1beta import (
    GenerativeServiceClient,
    GenerateContentRequest, GenerationConfig
)
from PIL import Image
from io import BytesIO

# === Load biến môi trường ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# === Cấu hình Gemini Client ===
client = GenerativeServiceClient(
    client_options=ClientOptions(api_key=GEMINI_API_KEY)
)

# === Tạo ảnh từ Gemini ===
async def generate_gemini_image(prompt):
    try:
        request = GenerateContentRequest(
            model="models/gemini-2.0-pro-preview-image",
            contents=prompt,  # ✅ CHỈ truyền chuỗi (str), không phải Content/Part
            generation_config=GenerationConfig(response_mime_type=["image"])
        )
        response = client.generate_content(request=request)

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    file_path = "gemini_image.png"
                    with open(file_path, "wb") as f:
                        f.write(part.inline_data.data)
                    return file_path
    except Exception as e:
        print("Gemini error:", e)
    return None

# === Xử lý lệnh /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để tạo ảnh bằng Gemini!")

# === Xử lý nội dung người dùng ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("⚠️ Prompt không được để trống.")
        return

    await update.message.reply_text("🧠 Đang tạo ảnh bằng Gemini...")
    image_path = await generate_gemini_image(prompt)

    if image_path:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini 2.0")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh từ Gemini.")

# === Khởi chạy bot bằng Webhook ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )
