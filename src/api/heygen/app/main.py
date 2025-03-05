from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QARequest(BaseModel):
    no: int
    question: str
    answer: str

class VideoResponse(BaseModel):
    video_url: str

@app.post("/generate_video", response_model=VideoResponse)
def generate_video(request: QARequest):
    # Process function logic goes here
    return VideoResponse(video_url="")
