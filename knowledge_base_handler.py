"""
Knowledge Base Handler for AI Support Bot
This module handles document ingestion, vector database operations, 
and knowledge retrieval using LangChain and ChromaDB.
"""

import os
import logging
from typing import List, Dict, Any

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
KNOWLEDGE_BASE_DIR = "knowledge_base"
CHROMA_PERSIST_DIR = "chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class KnowledgeBaseHandler:
    """Handles document processing and retrieval for the AI support bot."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the knowledge base handler.
        
        Args:
            openai_api_key: API key for OpenAI (defaults to env var)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.vectorstore = None
        self.documents = []
        self.processed_files = set()
        
        # Create directories if they don't exist
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a document from a file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Create a Document object
            doc = Document(page_content=text, metadata={"source": file_path})
            
            # Split the document into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            logger.info(f"Loaded and split {file_path} into {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return []
    
    def load_knowledge_base(self) -> None:
        """Load all documents from the knowledge base directory."""
        try:
            # Get all files in the knowledge base directory
            files = [os.path.join(KNOWLEDGE_BASE_DIR, f) for f in os.listdir(KNOWLEDGE_BASE_DIR) 
                     if os.path.isfile(os.path.join(KNOWLEDGE_BASE_DIR, f)) and
                     f.endswith(('.txt', '.md'))]
            
            # Process only new files
            new_files = [f for f in files if f not in self.processed_files]
            
            if not new_files:
                logger.info("No new files to process")
                return
            
            all_chunks = []
            
            # Process each new file
            for file_path in new_files:
                chunks = self.load_document(file_path)
                all_chunks.extend(chunks)
                self.processed_files.add(file_path)
            
            self.documents.extend(all_chunks)
            
            # Create or update the vector store
            if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
                # Add documents to existing DB
                vectorstore = Chroma(
                    persist_directory=CHROMA_PERSIST_DIR,
                    embedding_function=self.embeddings
                )
                vectorstore.add_documents(all_chunks)
            else:
                # Create new DB
                vectorstore = Chroma.from_documents(
                    documents=all_chunks,
                    embedding=self.embeddings,
                    persist_directory=CHROMA_PERSIST_DIR
                )
            
            vectorstore.persist()
            self.vectorstore = vectorstore
            
            logger.info(f"Successfully loaded {len(all_chunks)} chunks from {len(new_files)} files")
        
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
    
    def get_retriever(self):
        """Get the retriever for the vectorstore."""
        if not self.vectorstore:
            # Try to load existing DB
            if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
                self.vectorstore = Chroma(
                    persist_directory=CHROMA_PERSIST_DIR,
                    embedding_function=self.embeddings
                )
            else:
                # Load documents first
                self.load_knowledge_base()
        
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
    
    def query_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Query the knowledge base with a user question.
        
        Args:
            query: User question
            
        Returns:
            Dictionary with answer and source documents
        """
        try:
            # Ensure the vectorstore is loaded
            if not self.vectorstore:
                # Try to load existing DB
                if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
                    self.vectorstore = Chroma(
                        persist_directory=CHROMA_PERSIST_DIR,
                        embedding_function=self.embeddings
                    )
                else:
                    # Load documents first
                    self.load_knowledge_base()
                    
                    if not self.vectorstore:
                        raise ValueError("Failed to initialize vector store")
            
            # Get relevant documents from the retriever
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            docs = retriever.get_relevant_documents(query)
            
            if not docs:
                return {
                    "answer": "I couldn't find any relevant information in my knowledge base for that question.",
                    "sources": []
                }
            
            # Prepare context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create a prompt that includes the retrieved context
            prompt = f"""
            Answer the following question based on the provided context. If the context doesn't contain relevant information, say so.
            
            Context:
            {context}
            
            Question: {query}
            
            Answer:
            """
            
            # Use OpenAI to generate an answer based on the context
            llm = ChatOpenAI(
                model="gpt-4o",  # the newest OpenAI model
                temperature=0,
                openai_api_key=self.openai_api_key
            )
            
            messages = [
                {"role": "system", "content": "You are an AI assistant answering questions based on provided context."},
                {"role": "user", "content": prompt}
            ]
            
            response = llm.invoke(messages)
            answer = response.content
            
            # Extract source information
            sources = []
            for doc in docs:
                if 'source' in doc.metadata:
                    source_path = doc.metadata['source']
                    source_name = os.path.basename(source_path)
                    if source_name not in sources:
                        sources.append(source_name)
            
            return {
                "answer": answer,
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return {
                "answer": f"I encountered an error while searching the knowledge base: {str(e)}",
                "sources": []
            }