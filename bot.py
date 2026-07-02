import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from ollama_client import OllamaClient

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables.")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:latest")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Ollama client
ollama = OllamaClient(OLLAMA_URL)

# --- User State Management ---
user_sessions = {}

def get_user_session(user_id):
    """Get or create a user session."""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'model': DEFAULT_MODEL,
            'system_prompt': None,
            'history': [],
            'awaiting_system_prompt': False
        }
    return user_sessions[user_id]

# --- Keyboard Builders ---
def get_main_keyboard():
    """Main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🤖 Change Model", callback_data="change_model")],
        [InlineKeyboardButton("📝 Set System Prompt", callback_data="set_system_prompt")],
        [InlineKeyboardButton("🗑️ Clear History", callback_data="clear_history")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_model_keyboard(models, current_model):
    """Keyboard for model selection."""
    keyboard = []
    for model in models:
        # Add a checkmark next to the current model
        display_name = f"{model} ✅" if model == current_model else model
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"model_{model}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    user_id = user.id
    session = get_user_session(user_id)
    
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        f"Welcome to your **Local LLM Bot**! 🤖\n\n"
        f"This bot connects to a local Ollama instance running on your server.\n"
        f"Current model: `{session['model']}`\n\n"
        f"💬 Just send any message to chat with the AI.\n"
        f"Use the menu below to manage your session:"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
🤖 **Local LLM Bot - Help**

**Commands:**
/start - Start the bot and show menu
/help - Show this help message
/about - About this bot
/cancel - Cancel current operation

**Features:**
• **Chat with AI**: Just send any message
• **Change Model**: Switch between different Ollama models
• **System Prompt**: Set custom instructions for the AI
• **Clear History**: Reset conversation context

**How it works:**
1. This bot connects to your local Ollama server
2. No API keys required - everything runs locally
3. Each user has their own conversation history
4. History is maintained per session

**Tips:**
• Use `/cancel` to stop any ongoing operation
• Set a system prompt to customize the AI's behavior
• Clear history when you want to start fresh
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = """
⚡ **Local LLM Bot v1.0**

A Telegram interface for running open-source LLMs locally using Ollama.

**Features:**
• Connect to local Ollama server
• No external API keys needed
• Multiple model support
• Custom system prompts
• Conversation history

**Tech Stack:**
• Python + python-telegram-bot
• Ollama for LLM inference
• Deployed on Railway

**Developer:** @YourUsername
**Source Code:** github.com/YourUsername/LocalLLMBot
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session['awaiting_system_prompt'] = False
    
    await update.message.reply_text(
        "🔄 Operation cancelled. Send a message to chat with the AI, or use the menu.",
        reply_markup=get_main_keyboard()
    )

# --- Callback Handlers ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    session = get_user_session(user_id)

    if data == "back_to_main":
        await query.edit_message_text(
            f"🏠 **Main Menu**\n\n"
            f"Current model: `{session['model']}`\n"
            f"History length: {len(session['history'])} messages\n\n"
            f"Send a message to chat with the AI, or use the buttons:",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    if data == "change_model":
        # Get available models from Ollama
        models = ollama.list_models()
        if not models:
            await query.edit_message_text(
                "❌ Could not fetch models from Ollama server.\n"
                "Please ensure Ollama is running and accessible.",
                reply_markup=get_main_keyboard()
            )
            return
        
        await query.edit_message_text(
            "🤖 **Select a Model**\n\n"
            "Choose the model you want to use:",
            parse_mode='Markdown',
            reply_markup=get_model_keyboard(models, session['model'])
        )
        return

    if data.startswith("model_"):
        model_name = data.replace("model_", "")
        session['model'] = model_name
        await query.edit_message_text(
            f"✅ Model changed to: `{model_name}`",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    if data == "set_system_prompt":
        session['awaiting_system_prompt'] = True
        await query.edit_message_text(
            "📝 **Set System Prompt**\n\n"
            "Send me the system prompt you want to use.\n"
            "This will guide the AI's behavior for your session.\n\n"
            "Examples:\n"
            "• *You are a helpful assistant.*\n"
            "• *You are a coding expert. Provide code examples.*\n"
            "• *You are a creative writer.*\n\n"
            "Type `/cancel` to stop.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    if data == "clear_history":
        session['history'] = []
        await query.edit_message_text(
            "🗑️ Conversation history cleared!\n\n"
            "Start fresh with a new chat.",
            reply_markup=get_main_keyboard()
        )
        return

    if data == "help":
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages (chat or system prompt)."""
    user_id = update.effective_user.id
    user_message = update.message.text
    session = get_user_session(user_id)

    # Check if user is setting a system prompt
    if session.get('awaiting_system_prompt', False):
        session['system_prompt'] = user_message
        session['awaiting_system_prompt'] = False
        await update.message.reply_text(
            f"✅ System prompt set successfully!\n\n"
            f"**Current prompt:**\n{user_message}\n\n"
            f"Now send any message to chat with the AI.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    # Show typing indicator
    await update.message.chat.send_action(action="typing")

    # Prepare the prompt with context
    prompt = user_message
    model = session['model']
    system_prompt = session.get('system_prompt')
    history = session.get('history', [])

    try:
        # Generate response from Ollama
        response = ollama.generate(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            history=history[-MAX_HISTORY*2:] if history else None  # Keep last N messages
        )
    except Exception as e:
        logger.error(f"Error in generate: {str(e)}")
        await update.message.reply_text(
            f"❌ Error generating response: {str(e)}\n\n"
            f"Please check that Ollama is running on your server.",
            reply_markup=get_main_keyboard()
        )
        return

    # Update history (store as messages)
    session['history'].append({"role": "user", "content": prompt})
    session['history'].append({"role": "assistant", "content": response})
    
    # Trim history if too long
    if len(session['history']) > MAX_HISTORY * 2:
        session['history'] = session['history'][-MAX_HISTORY * 2:]

    # Send response (split if too long for Telegram)
    if len(response) > 4000:
        # Split into chunks
        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            await update.message.reply_text(
                chunk,
                reply_markup=get_main_keyboard() if chunk == chunks[-1] else None
            )
    else:
        await update.message.reply_text(
            response,
            reply_markup=get_main_keyboard()
        )

# --- Main Function ---
def main():
    """Start the bot."""
    logger.info("Starting Local LLM Bot...")
    logger.info(f"Connecting to Ollama at: {OLLAMA_URL}")
    
    # Test connection to Ollama
    models = ollama.list_models()
    if models:
        logger.info(f"✅ Connected to Ollama. Available models: {', '.join(models)}")
    else:
        logger.warning("⚠️ Could not connect to Ollama or no models found. Ensure it's running.")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(button_handler))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running and polling for updates...")
    application.run_polling()

if __name__ == '__main__':
    main()
