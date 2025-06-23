import logging
import aiohttp
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
TELEGRAM_BOT_TOKEN = "8083456157:AAGqAGyjGCAYEhZvqitOFqznlteu8DTX09Q"
GROQ_API_KEY = "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"
GROQ_MODEL = "llama3-8b-8192"  # or llama3-70b-8192

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def query_groq(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return "".join(f"\\{c}" if c in escape_chars else c for c in text)

def detect_emoji(text: str, is_code: bool) -> str:
    # Simple heuristic to add emojis by context
    text_lower = text.lower()
    if is_code:
        return "💻 "  # Code emoji prefix
    if any(greet in text_lower for greet in ["hello", "hi", "hey", "greetings"]):
        return "👋 "
    if any(err in text_lower for err in ["error", "fail", "warning", "sorry"]):
        return "⚠️ "
    if any(ask in text_lower for ask in ["how to", "explain", "what is", "help"]):
        return "📘 "
    # default general info emoji
    return "✨ "

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any message.\n"
        "If you ask for code, I will format code snippets separately so you can copy them easily."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action("typing")
    try:
        response = await query_groq(user_input)

        parts = response.split("```")

        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            if i % 2 == 0:
                # normal text
                emoji = detect_emoji(part, is_code=False)
                await update.message.reply_text(f"{emoji}{part}")
            else:
                # code block
                emoji = detect_emoji(part, is_code=True)
                escaped_code = escape_markdown(part)
                code_message = f"{emoji}```\n{escaped_code}\n```"
                await update.message.reply_text(code_message, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
