import sys
import os
    
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.chromadb_functions import * 
from models.gpt_models import correct_text_or_audio

# Load environment variables
load_dotenv(".env")

# ChromaDB Configuration
collection_path = "vector_database"
collection_name = os.getenv("CHROMADB_COLLECTION_NAME")
embedding_func = define_embedding_function(api_key=os.getenv("OPENAI_API_KEY"), model_name=os.getenv("EMBEDDING_MODEL"))
similarity_method = os.getenv("SIMILARITY_METHOD")
chromadb_collection = get_chroma_collection(collection_path, collection_name, embedding_func, similarity_method)

ask_again = "Xin lỗi bà con, Đạm Cà Mau hiện tại chưa thể trả lời câu hỏi này, kính mong bà con hãy hỏi câu hỏi khác."

# Initialize FastAPI
app = FastAPI()

# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=10)

# Define input model
class SearchQuery(BaseModel):
    text: str
    audio: str
    
class QuestionResponse(BaseModel):
    question_id: str
    answer: str
    
class Add_Question(BaseModel):
    no: str
    question: str
    

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chat API is ready!"}


# Function to run blocking ChromaDB query in thread pool
async def query_chromadb(corrected_text):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: chromadb_collection.query(
        query_texts=[corrected_text.content],
        n_results=1
    ))


@app.post("/api/video-search")
async def video_search(query: SearchQuery):
    if not query.text and not query.audio:
        return QuestionResponse(question_id = "-1", answer = ask_again) 
    
    # Correct text asynchronously
    corrected_text = await asyncio.to_thread(correct_text_or_audio, query.text, query.audio)

    try:
        # Perform ChromaDB query asynchronously
        results = await query_chromadb(corrected_text)

        if results["distances"][0][0] > 0.6:
            return QuestionResponse(question_id = "-1", answer = ask_again)
        else:
            return QuestionResponse(question_id = results["ids"][0][0], answer = results["documents"][0][0])

    except Exception as e:
        print(f"Error: {e}")
        return QuestionResponse(question_id = "-1", answer = ask_again)
    

@app.post("/api/add-question")
async def add_question(query: Add_Question):
    try:
        # Add data to ChromaDB asynchronously
        await asyncio.to_thread(
            chromadb_collection.add,
            documents=[query.question],
            metadatas=[{"id": query.no}],
            ids=[query.no]
        )

        return JSONResponse(
            content={"status": "success", "message": "Question added successfully", "question_id": query.no},
            status_code=200
        )

    except Exception as e:
        print(f"Error adding question: {e}")
        return JSONResponse(
            content={"status": "failed", "message": str(e), "question_id": query.no},
            status_code=500
        )
    


