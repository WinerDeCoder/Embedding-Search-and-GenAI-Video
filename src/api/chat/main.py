import os
import asyncio
import uuid
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
collection_path = "/app/vector_database"
collection_name = os.getenv("CHROMADB_COLLECTION_NAME")
embedding_func = define_embedding_function(api_key=os.getenv("OPENAI_API_KEY"), model_name=os.getenv("EMBEDDING_MODEL"))
similarity_method = os.getenv("SIMILARITY_METHOD")
chromadb_collection = get_chroma_collection(collection_path, collection_name, embedding_func, similarity_method)

ask_again = "U là trời, câu hỏi này coi vậy mà khó ha, thôi từ từ anh hai cà mau trả lời sau nha, hỏi câu khác giúp mình nha."

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
    num_query: int
    
class QuestionResponse(BaseModel):
    question_id: str
    answer: str

# Function to run blocking ChromaDB query in thread pool
async def query_chromadb(corrected_text, num_query):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: chromadb_collection.query(
        query_texts= [corrected_text],
        n_results= num_query
    ))


@app.post("/api/video-search")
async def video_search(query: SearchQuery):
    if not query.text and not query.audio:
        return JSONResponse(content={"status": "error", "message": "Empty input"}, status_code=400)
    
    # Correct text asynchronously
    corrected_text = await asyncio.to_thread(correct_text_or_audio, query.text, query.audio)

    try:
        # Perform ChromaDB query asynchronously
        results = await query_chromadb(corrected_text, query.num_query)

        paired_data = []
        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            paired_data.append({
                "uuid": meta.get("uuid", ""),
                "document": doc,
                "distance": dist
            })
            
        return JSONResponse(content={"status": "success", "input_text": corrected_text, "data": paired_data}, status_code=200)
    
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    


#Endpoint to add question to database
class Add_Question(BaseModel):
    uuid: str
    question: str

@app.post("/api/add-question")
async def add_question(query: Add_Question):
    try:
        # Add data to ChromaDB asynchronously
        await asyncio.to_thread(
            chromadb_collection.add,
            documents=[query.question],
            metadatas=[{"uuid": query.uuid}],
            ids=[str(uuid.uuid4())]
        )

        return JSONResponse(
            content={"status": "success", "message": "Question added successfully", "uuid": query.uuid},
            status_code=200
        )

    except Exception as e:
        print(f"Error adding question: {e}")
        return JSONResponse(
            content={"status": "failed", "message": str(e), "uuid": query.uuid},
            status_code=500
        )
        

#EndPoint to retrieve all data
@app.get("/api/get-all-data")
def get_all_data():
    try:
        # Get all data from ChromaDB
        data = chromadb_collection.get()

        # Ensure we have the correct fields
        documents = data.get("documents", [])
        metadatas = [item['uuid'] for item in data["metadatas"]]
        
        # Pair documents with their corresponding UUIDs
        paired_data = [
            {"document": doc, "uuid": meta}
            for doc, meta in zip(documents, metadatas)
        ]

        return JSONResponse(content={"status": "success", "data": paired_data}, status_code=200)

    except Exception as e:
        
        return JSONResponse(content={"status": "failed", "message": str(e)}, status_code=500)
    

  
# Request model for updating documents
class UpdateRequest(BaseModel):
    uuid: str
    question: str

@app.put("/api/update-data")
def update_data(request: UpdateRequest):
    try:
        
        question_id = chromadb_collection.get(where={"uuid": request.uuid})
        
        if len(question_id['ids']) ==0:
            return JSONResponse(content={"status": "Invalid", "message": "UUID not found", "uuid": request.uuid}, status_code=404)
        
        
        # Perform update in ChromaDB
        chromadb_collection.update(
            ids=[question_id['ids'][0]],
            documents=[request.question]
        )

        return JSONResponse(content={"status": "success", "message": "Data updated successfully", "uuid": request.uuid}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"status": "failed", "message": str(e), "uuid": request.uuid}, status_code=500)
    
    
    


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
    uuid: str # List of IDs to delete

@app.delete("/api/delete-item")
def delete_by_ids(request: DeleteIDsRequest):
    try:
        
        question_id = chromadb_collection.get(where={"uuid": request.uuid})
        
        if len(question_id['ids']) ==0:
            return JSONResponse(content={"status": "Invalid", "message": "UUID not found", "uuid": request.uuid}, status_code=404)
        

        # Delete the requested IDs from ChromaDB
        chromadb_collection.delete(ids=[question_id['ids'][0]])

        return JSONResponse(
            content={"status": "success", "message": "Deleted successfully", "uuid": request.uuid},
            status_code=200
        )

    except Exception as e:
        print(f"Error deleting IDs: {e}")
        return JSONResponse(
            content={"status": "failed", "message": str(e)},
            status_code=500
        )


