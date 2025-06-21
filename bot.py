import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.ext import WebhookHandler
from dotenv import load_dotenv

from google.api_core.client_options import ClientOptions
from google.ai.generativelanguage_v1beta import (
    GenerativeServiceClient, Content, Part,
    GenerateContentRequest, GenerationConfig
)
from PIL import Image
from io import BytesIO

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ví dụ: https://yourdomain.up.railway.app

# Gemini client
client = GenerativeServiceClient(
    client_options=ClientOptions(api_key=GEMINI_API_KEY)
)

# Hàm sinh ảnh từ Gemini
async def generate_gemini_image(prompt):
    try:
        request = GenerateContentRequest(
            model="models/gemini-2.0-pro-preview-image",
            contents=[Content(role="user", parts=[Part(text=prompt)])],
            generation_config=GenerationConfig(response_mime_type=["image"])
        )
        response = client.generate_content(request=request)
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    file_path = "gemini_output.png"
                    with open(file_path, "wb") as f:
                        f.write(part.inline_data.data)
                    return file_path
    except Exception as e:
        print("Gemini error:", e)
    return None

# Xử lý /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi mình prompt mô tả hình ảnh!")

# Xử lý prompt
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    await update.message.reply_text("✨ Đang tạo ảnh bằng Gemini...")
    path = await generate_gemini_image(prompt)
    if path:
        with open(path, "rb") as img:
            await update.message.reply_photo(photo=img, caption="🟡 Gemini 2.0")
    else:
        await update.message.reply_text("❌ Không tạo được ảnh.")

# Khởi chạy webhook
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).webhook_url(WEBHOOK_URL).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    main()
