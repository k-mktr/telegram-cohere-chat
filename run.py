import re
import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import cohere
import cohere_config as config

# Constants
MAX_MESSAGE_LENGTH = 4096
CHAT_HISTORY_FILE_TEMPLATE = "chat_history_{}.json"

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize Cohere client
co = cohere.Client(api_key=config.API_KEY)

# Global variable to store the state of web search
enable_web_search = True

def markdown_to_html(text):
    # Convert Markdown bold (**text**) to HTML bold (<b>text</b>)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert Markdown headings (## Heading) to bold text instead of HTML headings
    for i in range(6, 0, -1):
        text = re.sub(r'^#{' + str(i) + r'}\s*(.*?)\s*$', r'<b>\1</b>', text, flags=re.MULTILINE)
    return text

def load_chat_history(chat_id):
    try:
        with open(f"chat_history_{chat_id}.json", "r") as file:
            data = file.read().strip()
            if not data:  # Check if the file is empty
                return []
            return json.loads(data)
    except FileNotFoundError:
        return []  # Return an empty list if no history file exists
    except json.JSONDecodeError:
        logging.error(f"Corrupted chat history for user {chat_id}. Starting with an empty history.")
        return []  # Return an empty list if the file is corrupted or contains invalid JSON

def save_chat_history(chat_id, chat_history):
    with open(f"chat_history_{chat_id}.json", "w") as file:
        json.dump(chat_history, file, indent=4)

async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton(f"{'🟢' if enable_web_search else '🔴'} Web Search", callback_data='toggle_web_search')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! I am your personal AI assistant, powered by Cohere. How can I assist you today?",
        reply_markup=reply_markup
    )

def safe_split_html(text, max_length=4096):
    parts = []
    while len(text) > max_length:
        split_point = text.rfind(' ', 0, max_length)
        if split_point == -1:
            split_point = max_length
        parts.append(text[:split_point])
        text = text[split_point:].lstrip()
    parts.append(text)
    return parts

async def handle_message(update: Update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check authorization
    if (str(chat_id) not in config.ALLOWED_GROUP_IDS and 
        str(user_id) not in config.ALLOWED_USER_IDS):
        await update.message.reply_text("Unauthorized user or group.")
        return

    # Check if the message is from a group
    if update.effective_chat.type in ['group', 'supergroup']:
        # Check if the bot is mentioned
        if context.bot.username in update.message.text:
            # Remove the bot's username from the message
            input_text = update.message.text.replace(f'@{context.bot.username}', '').strip()
        else:
            # If the bot is not mentioned, ignore the message
            return
    else:
        # For private chats, process as before
        input_text = update.message.text

    chat_history = load_chat_history(chat_id)
    response, sources, updated_history = await generate_response_with_cohere(input_text, chat_history)
    save_chat_history(chat_id, updated_history)

    await send_response(update, response, sources)

async def send_response(update: Update, response: str, sources: list):
    html_response = markdown_to_html(response)
    keyboard = [[InlineKeyboardButton(f"{'🟢' if enable_web_search else '🔴'} Web Search", callback_data='toggle_web_search')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if len(html_response) > MAX_MESSAGE_LENGTH:
        parts = safe_split_html(html_response)
        for i, part in enumerate(parts):
            if i == len(parts) - 1 and sources:
                part += f"\n\n<b>Sources:</b>\n" + "\n\n".join(sources)
            await update.message.reply_text(part, reply_markup=reply_markup, parse_mode='HTML')
    else:
        if sources:
            html_response += f"\n\n<b>Sources:</b>\n" + "\n\n".join(sources)
        await update.message.reply_text(html_response, reply_markup=reply_markup, parse_mode='HTML')

async def generate_response_with_cohere(prompt_input, chat_history):
    logger.info("Generating response for input: %s", prompt_input)
    custom_system_prompt = "You are a helpful assistant. Your responsibility is to assist your USER to the best of your ability."
    selected_model = "command-r-plus"
    temperature = 0.5

    # Append new user input to chat history
    chat_history.append({"role": "USER", "content": prompt_input})

    chat_stream_params = {
        "chat_history": [{"role": message["role"].upper(), "message": message["content"]} for message in chat_history],
        "message": prompt_input,
        "model": selected_model,
        "temperature": temperature,
        "max_tokens": 2024
    }

    if enable_web_search:
        chat_stream_params["connectors"] = [{"id": "web-search"}]

    response_generator = co.chat_stream(**chat_stream_params)
    full_response = ""
    simplified_documents = []
    for part in response_generator:
        if hasattr(part, 'text'):
            full_response += part.text
        if hasattr(part, 'documents'):
            for doc in part.documents:
                simplified_documents.append(f"<a href='{doc['url']}'>{doc['title']}</a>")

    return full_response, simplified_documents, chat_history

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    global enable_web_search
    enable_web_search = not enable_web_search
    button_label = f"{'🟢' if enable_web_search else '🔴'} Web Search"
    keyboard = [[InlineKeyboardButton(button_label, callback_data='toggle_web_search')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

async def forget(update: Update, context):
    user_id = update.message.from_user.id
    try:
        os.remove(f"chat_history_{user_id}.json")
        await update.message.reply_text("I've forgotten our previous conversations!")
    except FileNotFoundError:
        await update.message.reply_text("No conversation history found.")


def main():
    logger.info("Starting bot...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("forget", forget))  # Register the new command handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()