import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import List

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


#Endpoint to chat
# Define input model
class SearchQuery(BaseModel):
    text: str
    audio: str
    
class QuestionResponse(BaseModel):
    question_id: str
    answer: str

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
    


#Endpoint to add question to database
class Add_Question(BaseModel):
    no: List[str]
    question: List[str]

@app.post("/api/add-question")
async def add_question(query: Add_Question):
    try:
        # Add data to ChromaDB asynchronously
        await asyncio.to_thread(
            chromadb_collection.add,
            documents=query.question,
            metadatas=[{"id": f"{i}"} for i in query.no],
            ids=query.no
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
        
        
#EndPoint to retrieve all data
@app.get("/api/get-all-data")
def get_all_data():
    try:
        # Get all data from ChromaDB
        data = chromadb_collection.get()

        # Filter only required fields
        filtered_data = {
            "ids": data.get("ids", []),
            "documents": data.get("documents", []),
            "metadatas": data.get("metadatas", [])
        }

        return JSONResponse(content={"status": "success", "data": filtered_data}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"status": "failed", "message": str(e)}, status_code=500)
    

  
# Request model for updating documents
class UpdateRequest(BaseModel):
    ids: List[str]
    documents: List[str]

@app.put("/api/update-data")
def update_data(request: UpdateRequest):
    try:
        # Ensure ids and documents have the same length
        if len(request.ids) != len(request.documents):
            return JSONResponse(
                content={"status": "failed", "message": "Mismatch between IDs and documents count"},
                status_code=400
            )

        # Perform update in ChromaDB
        chromadb_collection.update(
            ids=request.ids,
            documents=request.documents
        )

        return JSONResponse(content={"status": "success", "message": "Data updated successfully"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"status": "failed", "message": str(e)}, status_code=500)
    
    
    


#EndPoint to delete all data
# Define request body model
class DeleteRequest(BaseModel):
    confirm: str  # Must be "yes" to proceed

@app.delete("/api/delete-all")
def delete_all_questions(request: DeleteRequest):
    try:
        # Ensure confirmation is correct
        if request.confirm.lower() != "yes":
            return JSONResponse(
                content={"status": "failed", "message": "Deletion not confirmed"},
                status_code=400
            )

        # Get all stored IDs
        all_ids = chromadb_collection.get()["ids"]
        
        if not all_ids:
            return JSONResponse(
                content={"status": "success", "message": "No data to delete"},
                status_code=200
            )
        
        # Delete all records
        chromadb_collection.delete(ids=all_ids)

        return JSONResponse(
            content={"status": "success", "message": "All records deleted"},
            status_code=200
        )
    
    except Exception as e:
        print(f"Error deleting records: {e}")
        return JSONResponse(
            content={"status": "failed", "message": str(e)},
            status_code=500
        )


#Endpoint to delete ids
# Define request body model
class DeleteIDsRequest(BaseModel):
    ids: List[str]  # List of IDs to delete

@app.delete("/api/delete-ids")
def delete_by_ids(request: DeleteIDsRequest):
    try:
        # Ensure the provided list is not empty
        if not request.ids:
            return JSONResponse(
                content={"status": "failed", "message": "No IDs provided"},
                status_code=400
            )

        # Delete the requested IDs from ChromaDB
        chromadb_collection.delete(ids=request.ids)

        return JSONResponse(
            content={"status": "success", "message": f"Deleted {len(request.ids)} items", "deleted_ids": request.ids},
            status_code=200
        )

    except Exception as e:
        print(f"Error deleting IDs: {e}")
        return JSONResponse(
            content={"status": "failed", "message": str(e)},
            status_code=500
        )


