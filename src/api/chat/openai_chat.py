import sys
import os

parent_path = os.path.abspath("../../..")  # Get absolute path of parent directory
if parent_path not in sys.path:  
    sys.path.append(parent_path)  # Add only if it's not already there

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from src.models.chromadb_functions import * 
from src.models.gpt_models import correct_text_or_audio

load_dotenv(".env")

collection_path     = "../../../data/vector_database"
collection_name     = os.getenv("CHROMADB_COLLECTION_NAME")
embedding_func      = define_embedding_function( api_key = os.getenv("OPENAI_API_KEY"), model_name = os.getenv("EMBEDDING_MODEL"))
similarity_method   = os.getenv("SIMILARITY_METHOD")
chromadb_collection = get_chroma_collection(collection_path, collection_name, embedding_func, similarity_method)


ask_again = "Xin lỗi bà con, Đạm Cà Mau hiện tại chưa thể trả lời câu hỏi này, kính mong bà con hãy hỏi câu hỏi khác."

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React's URL   localhost
    allow_credentials=False,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    return {"message": "Chat API is ready!"}


# Define the model for the input (request body)
class SearchQuery(BaseModel):
    text    :  str 
    audio   :  str 


# Define the video search endpoint
@app.post("/api/video-search")
async def video_search(query: SearchQuery):
    
    if query.text == "" and  query.audio == "" :
        return {"question_id": "-1", "answer": ask_again}
    
    input_text  = query.text
    input_audio = query.audio
    #print(f"Original text: {search_text}")
    

    # Correct the search text using GPT
    corrected_text = correct_text_or_audio(input_text = input_text, input_audio = input_audio)
    print(f"Corrected text: {corrected_text}")

    
    try:
        # Perform ChromaDB query to get similar embeddings
        results = chromadb_collection.query(
            query_texts=[corrected_text],
            n_results=1  # Return the most similar result (adjust as needed)
        )

        # Print results for debugging
        #print(results, type(results), results["metadatas"][0][0]["video"])
        if results["distances"][0][0] > 0.6:
            return {"question_id": "-1", "answer": ask_again}
        # Extract video path from metadata if present
        else:
            question_id = results["ids"][0][0]
            answer = results["documents"][0][0]
            return {"question_id": question_id, "answer": answer}

    except Exception as e:
        return {"question_id": "-1", "answer": ask_again}

# To run this app, use: `uvicorn server:app --reload`
