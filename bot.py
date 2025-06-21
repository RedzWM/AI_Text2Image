import os
import openai
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# === DALL·E ===
async def generate_dalle(prompt):
    try:
        response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        return response['data'][0]['url']
    except Exception as e:
        print("DALL·E Error:", e)
        return None

# === GEMINI ===
async def generate_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")
        response = model.generate_content(
            contents=prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type=["IMAGE"]
            )
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_data = part.inline_data.data
                # Lưu ảnh tạm vào file để gửi
                with open("gemini_temp.png", "wb") as f:
                    f.write(image_data)
                return "gemini_temp.png"
        return None
    except Exception as e:
        print("Gemini Error:", e)
        return None

# === HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi một prompt mô tả hình ảnh bạn muốn tạo!")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🎨 Đang tạo ảnh từ OpenAI và Gemini...")

    dalle = await generate_dalle(prompt)
    gemini_path = await generate_gemini(prompt)

    if dalle:
        await update.message.reply_photo(photo=dalle, caption="🟢 OpenAI (DALL·E)")
    if gemini_path:
        with open(gemini_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption="🟡 Google Gemini")

    if not dalle and not gemini_path:
        await update.message.reply_text("⚠️ Không tạo được ảnh. Kiểm tra API key.")

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.run_polling()
