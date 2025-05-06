"""
Command-line interface for the AI Support Bot.
Run this file directly to interact with the bot in the terminal.
"""

import os
import time
from token_utils import count_tokens, log_message

# LangChain imports - using the newer modular structure
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ANSI color codes for terminal output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
ENDC = "\033[0m"

def print_header():
    """Print a stylish header for the CLI application."""
    print(f"\n{MAGENTA}{BOLD}{'=' * 60}{ENDC}")
    print(f"{MAGENTA}{BOLD}{'Etherius AI Support Bot - CLI Version':^60}{ENDC}")
    print(f"{MAGENTA}{BOLD}{'=' * 60}{ENDC}")
    print(f"{CYAN}Type your questions below. Type 'exit' or 'quit' to end the session.{ENDC}\n")

def main():
    """Main function to run the CLI bot."""
    # Initialize with OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print(f"{YELLOW}Warning: OPENAI_API_KEY not found in environment variables.{ENDC}")
        return
    
    # Constants
    KNOWLEDGE_BASE_DIR = "knowledge_base"
    CHROMA_PERSIST_DIR = "chroma_db"
    MODEL_NAME = "gpt-4o"  # the newest OpenAI model
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    # Initialize text splitter for document processing
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    # Check if Chroma database exists, otherwise create it
    print(f"{BLUE}Initializing knowledge base...{ENDC}")
    
    if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
        # Load existing database
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings
        )
        print(f"{GREEN}Loaded existing knowledge base.{ENDC}")
    else:
        print(f"{YELLOW}Creating new knowledge base...{ENDC}")
        # Load documents from knowledge base directory
        documents = []
        if os.path.exists(KNOWLEDGE_BASE_DIR):
            files = [os.path.join(KNOWLEDGE_BASE_DIR, f) for f in os.listdir(KNOWLEDGE_BASE_DIR) 
                    if os.path.isfile(os.path.join(KNOWLEDGE_BASE_DIR, f)) and
                    f.endswith(('.txt', '.md'))]
            
            for file_path in files:
                try:
                    print(f"{BLUE}Loading {file_path}...{ENDC}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    # Create a Document object
                    doc = Document(page_content=text, metadata={"source": file_path})
                    
                    # Split the document into chunks
                    chunks = text_splitter.split_documents([doc])
                    documents.extend(chunks)
                    
                    print(f"{GREEN}Loaded and split {file_path} into {len(chunks)} chunks.{ENDC}")
                except Exception as e:
                    print(f"{YELLOW}Error loading document {file_path}: {str(e)}{ENDC}")
        
        # Create vector store
        if documents:
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=CHROMA_PERSIST_DIR
            )
            print(f"{GREEN}Created new knowledge base with {len(documents)} chunks.{ENDC}")
        else:
            print(f"{YELLOW}No documents found. Creating empty knowledge base.{ENDC}")
            vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=embeddings
            )
    
    # Initialize retriever and LLM
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        openai_api_key=openai_api_key
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Print header
    print_header()
    
    # Main chat loop
    try:
        while True:
            # Get user input
            user_input = input(f"{BOLD}You: {ENDC}")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print(f"\n{GREEN}Thank you for using Etherius AI Support Bot. Goodbye!{ENDC}")
                break
            
            if not user_input.strip():
                continue
            
            # Log user message and count tokens
            user_tokens = log_message("user", user_input, MODEL_NAME)
            
            # Process query
            print(f"{BLUE}Thinking...{ENDC}")
            start_time = time.time()
            
            try:
                # Execute the query
                result = qa_chain(user_input)
                
                # Extract response and sources
                answer = result["result"]
                sources = []
                if 'source_documents' in result and result['source_documents']:
                    for doc in result['source_documents']:
                        if 'source' in doc.metadata:
                            source_path = doc.metadata['source']
                            source_name = os.path.basename(source_path)
                            if source_name not in sources:
                                sources.append(source_name)
                
                # Log assistant message and count tokens
                assistant_tokens = log_message("assistant", answer, MODEL_NAME)
                
                # Display response
                print(f"\n{BOLD}Bot: {ENDC}{answer}")
                
                # Display sources if available
                if sources:
                    source_text = ", ".join(sources)
                    print(f"\n{YELLOW}Sources: {source_text}{ENDC}")
                
                # Display token usage and response time
                processing_time = time.time() - start_time
                print(f"\n{CYAN}[Token usage - User: {user_tokens}, Assistant: {assistant_tokens}, "
                      f"Total: {user_tokens + assistant_tokens}] "
                      f"[Response time: {processing_time:.2f}s]{ENDC}")
            
            except Exception as e:
                print(f"\n{YELLOW}Error: {str(e)}{ENDC}")
    
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Chat session ended. Goodbye!{ENDC}")

if __name__ == "__main__":
    main()