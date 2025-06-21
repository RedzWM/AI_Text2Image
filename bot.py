import os
import openai
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

user_prompt_dict = {}

# === TẠO ẢNH VỚI OPENAI ===
async def generate_dalle(prompt):
    try:
        response = openai_client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        return response.data[0].url
    except openai.APIStatusError as e:
        print("DALL·E status error:", e.status_code, e.response)
    except Exception as e:
        print("DALL·E unexpected error:", e)
    return None

# === TẠO ẢNH VỚI GEMINI ===
async def generate_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            contents=[{"role": "user", "parts": [prompt]}],
            generation_config=GenerationConfig(response_mime_type=["image"])
        )
        for part in response.parts:
            if hasattr(part, "inline_data") and part.inline_data.data:
                image_data = part.inline_data.data
                file_path = "gemini_image.png"
                with open(file_path, "wb") as f:
                    f.write(image_data)
                return file_path
    except Exception as e:
        print("Gemini error:", e)
    return None

# === KHI NGƯỜI DÙNG GỬI PROMPT ===
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("⚠️ Prompt không được để trống.")
        return

    user_prompt_dict[update.effective_user.id] = prompt

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 OpenAI (DALL·E)", callback_data="use_openai")],
        [InlineKeyboardButton("🟡 Google Gemini", callback_data="use_gemini")]
    ])
    await update.message.reply_text(
        "🤖 Chọn nền tảng AI bạn muốn dùng để tạo ảnh:",
        reply_markup=keyboard
    )

# === KHI NGƯỜI DÙNG NHẤN NÚT CHỌN AI ===
async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prompt = user_prompt_dict.get(user_id)

    if not prompt:
        await query.edit_message_text("⚠️ Không tìm thấy prompt. Gửi lại nội dung mới.")
        return

    if query.data == "use_openai":
        await query.edit_message_text("🧠 Đang tạo ảnh với OpenAI...")
        image_url = await generate_dalle(prompt)
        if image_url:
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_url, caption="🟢 OpenAI (DALL·E v2)")
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="⚠️ OpenAI thất bại. Thử tạo bằng Gemini...")
            image_path = await generate_gemini(prompt)
            if image_path:
                with open(image_path, "rb") as img:
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption="🟡 Gemini (Fallback)")
            else:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Cả hai AI đều không thể tạo ảnh.")

    elif query.data == "use_gemini":
        await query.edit_message_text("🧠 Đang tạo ảnh với Gemini...")
        image_path = await generate_gemini(prompt)
        if image_path:
            with open(image_path, "rb") as img:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption="🟡 Google Gemini")
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="⚠️ Gemini thất bại. Thử tạo bằng OpenAI...")
            image_url = await generate_dalle(prompt)
            if image_url:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_url, caption="🟢 OpenAI (Fallback)")
            else:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Cả hai AI đều không thể tạo ảnh.")

# === LỆNH /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi prompt để bắt đầu tạo ảnh!")

# === CHẠY BOT ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_prompt))
    app.add_handler(CallbackQueryHandler(handle_selection))
    app.run_polling()
