import chromadb.utils.embedding_functions as embedding_functions
import os

from dotenv import load_dotenv
load_dotenv("../../.env")

#chroma-openai embedding define

def define_embedding_function(api_key, model_name):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name
                )
    
    return openai_ef