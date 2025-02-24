import chromadb.utils.embedding_functions as embedding_functions
import os

from dotenv import load_dotenv
load_dotenv("../../.env")

#chroma-openai embedding define

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=os.getenv("EMBEDDING_MODEL")
            )