import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

# .env faylini yuklaymiz
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men Gemini AI yordamida ishlaydigan aqlli assistentman. Savolingizni bering! 🚀")

@dp.message()
async def message_handler(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config=genai_types.GenerateContentConfig(
                system_instruction="Sen Telegram bot ichidagi professional va aqlli AI assistentsan. Foydalanuvchiga aniq va tushunarli javob ber."
            )
        )
        await message.reply(response.text, parse_mode="Markdown")
    except Exception as e:
        await message.reply("Xatolik yuz berdi. Qayta urinib ko'ring.")
        print(f"Xato: {e}")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())