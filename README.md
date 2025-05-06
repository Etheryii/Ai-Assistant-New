# Etherius AI Support Bot

A powerful AI support bot built with a futuristic space-themed UI, using OpenAI's GPT models for natural language processing and LangChain with ChromaDB for enhanced knowledge retrieval.

![Etherius AI Screenshot](https://raw.githubusercontent.com/your-username/etherius-ai/main/screenshot.png)

## Features

- 🚀 **Beautiful Futuristic UI** - Space-themed design with animated stars and glowing effects
- 🤖 **Advanced AI Responses** - Powered by OpenAI's GPT-4o model
- 📚 **Knowledge Base Integration** - Uses LangChain and ChromaDB for document retrieval
- 📊 **Token Usage Tracking** - Monitors and logs token usage for all interactions
- 💬 **Markdown Support** - Supports code blocks, links, and basic formatting in messages
- 🌐 **Web & CLI Interface** - Use in browser or via command line

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Backend**: Flask
- **AI**: OpenAI GPT-4o
- **Vector Database**: ChromaDB
- **Framework**: LangChain
- **Token Counter**: Tiktoken

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository (or fork it on Replit)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
### Usage

#### Web Interface

Run the Flask application:
```bash
python main.py
```
Or with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

Then open your browser to http://localhost:5000

#### Command Line Interface

For terminal-based interaction:
```bash
python cli_bot.py
```

## Knowledge Base

The bot uses documents in the `knowledge_base/` directory to answer questions. You can add your own documents:

1. Create text files (.txt) or markdown files (.md) in the `knowledge_base/` directory
2. The bot will automatically load and index these documents
3. Information from these documents will be used to answer user queries

Example structure:
```
knowledge_base/
  product_info.txt
  troubleshooting.txt
  faq.txt
```

## Customization

You can customize the appearance by modifying the CSS in `static/styles.css` and the behavior by editing `static/script.js`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the GPT models
- LangChain team for the framework
- ChromaDB for the vector database

---

Built with ❤️ by [Your Name]# Ai-Assistant-New
