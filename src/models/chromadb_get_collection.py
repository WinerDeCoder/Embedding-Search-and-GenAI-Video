import chromadb
import os

from dotenv import load_dotenv
load_dotenv("../../.env")

#get chromadb collection
def get_chroma_collection(collection_path, collection_name, embedding_func, similarity_method):
    #Load chromadb by path
    client = chromadb.PersistentClient(path=collection_path)
    #retrieve collection
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_func, metadata={"hnsw:space": similarity_method})
    return collection