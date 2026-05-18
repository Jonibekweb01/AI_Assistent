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

def markdown_to_html(text: str) -> str:
    """
    Gemini qaytargan Markdown matnini Telegram HTML formatiga xavfsiz o'tkazadi.
    Belgilar sababli bot qulashini 100% oldini oladi.
    """
    if not text:
        return ""
    
    # HTML maxsus belgilarini xavfsizlantirish (teglarga zarar yetmasligi uchun)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 1. Uchta backtick ichidagi kod bloklarini <pre><code> ga o'tkazish
    def code_block_sub(match):
        language = match.group(1).strip() if match.group(1) else ""
        code_content = match.group(2)
        if language:
            return f'<pre><code class="language-{language}">{code_content}</code></pre>'
        return f'<pre><code>{code_content}</code></pre>'
    
    text = re.sub(r'```(\w*)\n([\s\S]*?)```', code_block_sub, text)
    
    # 2. Bitta backtick ichidagi qisqa kodlarni <code> ga o'tkazish
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
    
    # 3. Qalin matnlarni (**matn**) <b>matn</b> ga o'tkazish
    text = re.sub(r'\*\*([\s\S]+?)\*\*', r'<b>\1</b>', text)
    
    # 4. Yotiq matnlarni (*matn* yoki _matn_) <i>matn</i> ga o'tkazish
    text = re.sub(r'\*([\s\S]+?)\*', r'<i>\1</i>', text)
    
    return text

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! Men Frontend dasturlash bo'yicha sizning shaxsiy mentoringiz va AI assistentingizman. "
        "React.js, Next.js, Tailwind CSS, JavaScript/TypeScript va toza kod yozish (Clean Code) bo'yicha "
        "ixtiyoriy savollaringizni bering! 🚀", 
        parse_mode="HTML"
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
                    "professional dasturchi va kuchli mentorsan. Sen Meta Academy, CoddyCamp kabi yetakchi "
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
            # Matnni HTML formatiga o'tkazamiz
            html_text = markdown_to_html(response.text)
            await message.reply(html_text, parse_mode="HTML")
        else:
            await message.reply("Kechirasiz, javob tayyorlashda muammo yuz berdi.", parse_mode="HTML")
            
    except Exception as e:
        await message.reply("Xatolik yuz berdi. Qayta urinib ko'ring.", parse_mode="HTML")
        print(f"Xato: {e}")

# Render port so'ragani uchun oddiy HTTP server xizmati
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

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