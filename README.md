# Telegram Cohere Chat

A simple Telegram bot leveraging the power of Cohere API for intelligent conversations.

## 🌟 Features

- 💬 **Chat Interaction**: Engage users in natural language conversations
- 🧠 **Cohere API Integration**: Advanced language processing capabilities
- 📜 **Chat History Management**: Improved context through conversation tracking
- 🔍 **Web Search Capability**: Provide relevant web information on demand
- 🔐 **User Authentication**: Ensure only authorized users can interact with the bot
- 👥 **Group Chat Support**: Interact with the bot in group chats by mentioning it

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Telegram Bot Token
- Cohere API Key

### Bot Configuration

1. Enable group privacy mode for your bot via BotFather:
   - Send `/setprivacy` to @BotFather
   - Select your bot
   - Choose 'Enable' to allow the bot to respond to messages in groups

2. Add the bot to your group and grant it admin rights for full functionality.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-cohere-chat.git
   cd telegram-cohere-chat
   ```

2. Install dependencies:
   ```bash
   pip install python-telegram-bot cohere -U
   ```

3. Set up configuration:
   - Fill in your Telegram Bot Token, Cohere API Key, Allowed User IDs, and Allowed Group IDs in `cohere_config.py`

## 🎮 Usage

1. Start the bot:
   ```bash
   python run.py
   ```

2. In private chats, simply send messages to the bot.
3. In group chats, mention the bot using its username (e.g., @YourBotName) to interact with it.

## 🛠️ Commands

- `/start`: Initialize the bot and get a welcome message
- `/forget`: Clear the chat history

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

## 📝 License

This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.

## 🙏 Acknowledgements

- [Cohere](https://cohere.ai/) for their powerful AI API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram bot framework