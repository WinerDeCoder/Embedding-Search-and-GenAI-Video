import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv

from openai import OpenAI


load_dotenv()

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

# Mount the videos directory for static serving
app.mount("/videos", StaticFiles(directory="/app/videos"), name="videos")  # for Docker (if using "app" directory)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# ChromaDB setup with OpenAI embeddings
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-3-large",
    api_key=OPENAI_API_KEY
)

# Initialize PersistentClient and create or retrieve collection
chroma_client = chromadb.PersistentClient(path="chromadb")
collection = chroma_client.get_or_create_collection(name="large", embedding_function=openai_ef, metadata={"hnsw:space": "cosine"})

# Define the model for the input (request body)
class SearchQuery(BaseModel):
    text: str

# Function to correct or enhance the input text using GPT
def correct_text_with_gpt(input_text: str) -> str:
    prompt = f"""Bạn là một giám thị tiếng Việt nghiêm khắc. Nhiệm vụ của bạn là chỉnh sửa câu hỏi đầu vào sao cho:
- Các từ viết sai chính tả phải được sửa đúng.
- Các từ không dấu phải được thêm dấu chính xác.
- Số lượng từ trong câu phải giữ nguyên, không được thêm hoặc bớt.
- Không thêm bất kỳ từ hay ký tự nào khác ngoài việc chỉnh sửa trong từ.

Hãy trả về câu hỏi đã chỉnh sửa, chỉ trả lời câu hỏi đã chỉnh sửa mà không giải thích gì thêm.
"""
    try:
        
        completion = client.chat.completions.create(
            model="gpt-4-mini",
            messages=[
                {"role": "developer", "content": f"{prompt}"},
                {
                    "role": "user",
                    "content": f"{input_text}"
                }
            ]
        )
        
        corrected_text = completion.choices[0].message
        return corrected_text
    except Exception as e:
        print(f"Error in GPT correction: {str(e)}")
        return input_text  # Fallback to the original text

# Define the video search endpoint
@app.post("/api/video-search")
async def video_search(query: SearchQuery):
    search_text = query.text
    #print(f"Original text: {search_text}")

    # Correct the search text using GPT
    corrected_text = correct_text_with_gpt(search_text)
    #print(f"Corrected text: {corrected_text}")

    ask_again = "Xin lỗi bà con, Đạm Cà Mau hiện tại chưa thể trả lời câu hỏi này, kính mong bà con hãy hỏi câu hỏi khác."
    try:
        # Perform ChromaDB query to get similar embeddings
        results = collection.query(
            query_texts=[corrected_text],
            n_results=1  # Return the most similar result (adjust as needed)
        )

        # Print results for debugging
        try:
            #print(results, type(results), results["metadatas"][0][0]["video"])
            if results["distances"][0][0] > 0.7:
                return {"videoPath": "10.mp4", "answer": ask_again}
            # Extract video path from metadata if present
            if results and len(results['documents']) > 0:
                video_path = results["metadatas"][0][0]["video"]
                answer = results["documents"][0][0]
                #print(video_path)
                if video_path:
                    return {"videoPath": video_path, "answer": answer}
                else:
                    return {"videoPath": "10.mp4", "answer": ask_again}
            else:
                return {"videoPath": "10.mp4", "answer": ask_again}  # No matching video found
        except:
            return {"videoPath": "10.mp4", "answer": ask_again}
    except Exception as e:
        return {"videoPath": "10.mp4", "answer": ask_again}

# To run this app, use: `uvicorn server:app --reload`
