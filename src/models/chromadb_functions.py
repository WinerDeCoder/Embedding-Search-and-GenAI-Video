import chromadb
import os
import chromadb.utils.embedding_functions as embedding_functions


from dotenv import load_dotenv
load_dotenv("../../.env")


#chroma-openai embedding define
def define_embedding_function(api_key, model_name):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name
                )
    return openai_ef


#get chromadb collection
def get_chroma_collection(collection_path, collection_name, embedding_func, similarity_method):
    #Load chromadb by path
    client = chromadb.PersistentClient(path=collection_path)
    #retrieve collection
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_func, metadata={"hnsw:space": similarity_method})
    return collection