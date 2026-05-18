import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# .env yuklash
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men siz sozlangan maxsus yo'nalish bo'yicha AI assistentman. Savolingizni bering! 🚀")

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

# Render port so'ragani uchun oddiy HTTP server xizmati
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print("Dummy server started on port", port)
    server.serve_forever()

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    
    # Render o'chib qolmasligi uchun HTTP serverni alohida oqimda (Thread) yuritamiz
    server_thread = threading.Thread(target=run_health_server, daemon=True)
    server_thread.start()
    
    # Botni oddiy polling orqali ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())