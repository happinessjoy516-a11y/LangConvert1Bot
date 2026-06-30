import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from deep_translator import GoogleTranslator

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

# Popular languages for quick selection
POPULAR_LANGUAGES = {
    'en': '🇬🇧 English',
    'es': '🇪🇸 Spanish',
    'fr': '🇫🇷 French',
    'de': '🇩🇪 German',
    'it': '🇮🇹 Italian',
    'pt': '🇵🇹 Portuguese',
    'ru': '🇷🇺 Russian',
    'zh-CN': '🇨🇳 Chinese (Simplified)',
    'ja': '🇯🇵 Japanese',
    'ar': '🇸🇦 Arabic',
    'hi': '🇮🇳 Hindi',
    'ko': '🇰🇷 Korean',
    'nl': '🇳🇱 Dutch',
    'tr': '🇹🇷 Turkish',
    'vi': '🇻🇳 Vietnamese',
    'th': '🇹🇭 Thai',
    'id': '🇮🇩 Indonesian',
    'pl': '🇵🇱 Polish',
    'uk': '🇺🇦 Ukrainian',
    'he': '🇮🇱 Hebrew'
}

# Store user preferences (in production, use database)
user_languages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message with language selection."""
    user = update.effective_user
    welcome_text = f"""
🌍 **Welcome to LangConvert1Bot, {user.first_name}!**

I can translate text between any languages instantly.

📤 Send me any text and I'll translate it to your chosen language!

**Quick Commands:**
/start - Show this menu
/lang - Change target language
/langs - List all supported languages
/help - Show all commands

**Supported languages:** 100+ languages via Google Translate
"""
    await update.message.reply_text(welcome_text)


async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None) -> None:
    """Display language selection keyboard."""
    keyboard = []
    row = []
    for idx, (lang_code, lang_name) in enumerate(POPULAR_LANGUAGES.items()):
        row.append(InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}"))
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="lang_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = message or "🌐 **Select your target language:**"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection menu."""
    await show_language_menu(update, context)


async def langs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all supported languages."""
    lang_list = "\n".join([f"• {name}" for name in POPULAR_LANGUAGES.values()])
    await update.message.reply_text(
        f"📋 **Supported Languages:**\n\n{lang_list}\n\n"
        f"Use /lang to choose your target language!"
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses for language selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "lang_cancel":
        await query.edit_message_text("❌ Language selection cancelled.")
        return
    
    # Extract language code
    lang_code = query.data.replace("lang_", "")
    user_languages[user_id] = lang_code
    
    lang_name = POPULAR_LANGUAGES.get(lang_code, lang_code)
    await query.edit_message_text(
        f"✅ **Target language set to: {lang_name}**\n\n"
        f"Now send me any text to translate!"
    )


async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate user message to their selected language."""
    user_text = update.message.text
    user_id = update.effective_user.id
    
    # Get user's target language or default to English
    target_language = user_languages.get(user_id, 'en')
    target_name = POPULAR_LANGUAGES.get(target_language, target_language)
    
    try:
        # Use executor for synchronous translation API
        loop = asyncio.get_running_loop()
        translated_text = await loop.run_in_executor(
            None,
            lambda: GoogleTranslator(target=target_language).translate(user_text)
        )
        
        response = (
            f"<b>🔤 Original:</b>\n{user_text}\n\n"
            f"<b>🌐 Translation ({target_name}):</b>\n{translated_text}"
        )
        
        await update.message.reply_text(response, parse_mode="HTML")
        logger.info(f'Successful translation for user {user_id} to {target_language}')
        
    except Exception as e:
        logger.error(f'Translation error for user {user_id}: {str(e)}')
        await update.message.reply_text(
            "❌ Translation error. Please try again.\n"
            "Make sure your text is valid and try a different language."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
📖 **How to use LangConvert1Bot:**

1️⃣ Send me any text message
2️⃣ I'll translate it to your selected language
3️⃣ Get instant translation!

**Commands:**
/start - Welcome message
/lang - Choose target language
/langs - List all supported languages
/help - Show this help message

**Supported languages:** 100+ languages including:
English, Spanish, French, German, Chinese, Arabic, Hindi, Japanese, Korean, Russian, and more!

💡 **Tip:** Use /lang to change your target language anytime.
"""
    await update.message.reply_text(help_text)


def main() -> None:
    """Start the bot."""
    # Create Application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lang", lang_command))
    application.add_handler(CommandHandler("langs", langs_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for text messages (but not commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message))
    
    # Start the Bot
    logger.info("LangConvert1Bot started! Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == '__main__':
    main()
