# Local LLM Bot (Ollama)

A Telegram bot that connects to a local Ollama instance for private, offline LLM interactions.

## Features
- Connect to local Ollama server
- No external API keys required
- Multiple model support (Llama 3, Mistral, Phi, etc.)
- Custom system prompts
- Conversation history per user
- Model switching via menu

## Setup
1. Install Ollama on your server: https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Clone this repository
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with your bot token and Ollama URL
6. Run: `python bot.py`

## Environment Variables
- `BOT_TOKEN`: Your Telegram bot token
- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)
- `DEFAULT_MODEL`: Default model to use (default: llama3.2:latest)
- `MAX_HISTORY`: Max conversation history per user (default: 10)

## Deployment on Railway
1. Push code to GitHub
2. Connect repository to Railway
3. Add environment variables
4. Deploy!

**Note**: For Railway, you'll need to run Ollama separately or use a Railway service that supports it.
