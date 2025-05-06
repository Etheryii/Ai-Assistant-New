# Project Dependencies

For anyone cloning this project on GitHub, you'll need to install the following dependencies:

```bash
pip install chromadb email-validator flask gunicorn jinja2 langchain langchain-community langchain-core langchain-openai langchain-text-splitters openai psycopg2-binary tiktoken
```

## Environment Variables

You'll need to set the following environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Running the Application

To run the web interface:
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

To run the command-line interface:
```bash
python cli_bot.py
```