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

# Esiz kodda faqat dp.start_polling(bot) bor edi.
# Render o'chib qolmasligi uchun kichik veb-server ham qo'shib yuboramiz.
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    
    # Render port talab qilgani uchun fon rejimi xatoligini oldini olamiz
    import asyncio
    from aiogram.webhook.aiohttp_impl import SimpleRequestHandler
    from aiohttp import web
    
    # Render beradigan portni olamiz (bepul rejim uchun majburiy)
    port = int(os.getenv("PORT", 10000))
    app = web.Application()
    
    # Botni oddiy polling orqali ishga tushiramiz
    asyncio.create_task(dp.start_polling(bot))
    
    # Serverni fonda yuritib qo'yamiz (Render tekin tarifda o'chirib qo'ymasligi uchun)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    # Bot o'chib qolmasligi uchun cheksiz kutish rejimida ushlab turamiz
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())