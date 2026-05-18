import os
import asyncio
import re
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from http.server import BaseHTTPRequestHandler, HTTPServer

# .env yuklash
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def escape_markdown_v2(text: str) -> str:
    """
    Telegram MarkdownV2 formatida xatolik bermasligi uchun 
    kod bloklaridan tashqaridagi maxsus belgilarni ekranlaydi.
    """
    if not text:
        return ""
    # Kod bloklarini ajratib olamiz
    parts = re.split(r'(```[\s\S]*?```|`[^`\n]*`)', text)
    for i in range(len(parts)):
        # Agar bu oddiy matn bo'lsa (kod bloki bo'lmasa), belgilarni ekranlaymiz
        if not parts[i].startswith('`'):
            # MarkdownV2 uchun ekranlanishi shart bo'lgan belgilar
            escape_chars = r'_*[]()~>#+-=|{}.!'
            parts[i] = re.sub(r'([' + re.escape(escape_chars) + r'])', r'\\\1', parts[i])
    return "".join(parts)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! Men Frontend dasturlash bo'yicha sizning shaxsiy mentoringiz va AI assistentingizman. "
        "React.js, Next.js, Tailwind CSS, JavaScript/TypeScript va toza kod yozish (Clean Code) bo'yicha "
        "ixtiyoriy savollaringizni bering! 🚀"
    )

@dp.message()
async def message_handler(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        # Gemini modeliga so'rov yuborish
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config=genai_types.GenerateContentConfig(
                system_instruction=(
                    "Sen Frontend dasturlash (Frontend Engineering) sohasida 5 yildan ortiq tajribaga ega "
                    " professional dasturchi va kuchli mentorsan. Sen Meta Academy, CoddyCamp kabi yetakchi "
                    "IT akademiyalarda 500 dan ortiq shogird chiqargansan. Foydalanuvchilarga faqat quyidagi mavzularda yordam berasan:\n"
                    "1. Frontend texnologiyalari: HTML5, CSS3, JavaScript (ES6+), TypeScript, React.js, Next.js va Tailwind CSS.\n"
                    "2. Yaxshi amaliyotlar: Clean Code (toza kod yozish), arxitektura, komponentlarni optimallashtirish va UI/UX qonuniyatlari.\n"
                    "Har doim javoblaringda tushunarli kod namunalarini keltir, xatoliklarni topishda va kodni refaktor qilishda mentor kabi yo'nalish ber. "
                    "Agar foydalanuvchi frontend sohasiga umuman aloqador bo'lmagan (masalan, kulinariya, tarix yoki mutlaqo boshqa yo'nalishda) savol bersa, "
                    "muloyimlik bilan rad et va faqat Frontend dasturlash bo'yicha yordam bera olishingni eslat."
                )
            )
        )
        
        if response and response.text:
            # Telegram formatiga moslab belgilarni tozalaymiz
            safe_text = escape_markdown_v2(response.text)
            await message.reply(safe_text, parse_mode="MarkdownV2")
        else:
            await message.reply("Kechirasiz, javob tayyorlashda muammo yuz berdi.")
            
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

    # Render HEAD so'rovlarini ham yuborib turadi, xatolik chiqmasligi uchun qo'shildi
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

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
    
    # Botni polling orqali ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())