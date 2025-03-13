import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
import requests
from dotenv import load_dotenv
load_dotenv(".env")

app = FastAPI()


# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React's URL   localhost
    allow_credentials=False,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

#Payload
def payload_setting(title, script):
    
    payload = {
        "test": True,
        "caption": False,
        "title": title,
        "dimension": {
                "width": 1920,  # Fix
                "height": 1080  # fix
            },
        "variables": {
            "script": {
                "name": "script",
                "type": "text",
                "properties": {"content": script},
            }
        },
    }
    
    # payload = {
    #         "caption": False,  # Caption, maybe the subtile
    #         "title": title,  # Need to change , match the index of video
    #         "callback_id": "string",
    #         "dimension": {
    #             "width": 1024,  # Fix
    #             "height": 720  # fix
    #         },
    #         "video_inputs": [      # up to 50, don't know whether it is video setting or many video at a time
    #             {
    #                 "character": {
    #                     "type": "avatar",
    #                     "avatar_id": "Angela-inTshirt-20220820",
    #                     "avatar_style": "normal"
    #                 },
    #                 "voice": {
    #                     "type": "text",
    #                     "voice_id": "c6fb81520dcd42e0a02be231046a8639", #str
    #                     "input_text": script #str
    #                 },   # voice id Fixx
    #             }
    #         ],
    #         "callback_url": "string"
    #     }
    
    return payload


# General Define
heygen_api_key  = os.getenv("HEYGEN_API_KEY")
headers         = {"Accept": "application/json", "X-API-KEY": heygen_api_key}
template_id     = os.getenv("TEMPLATE_ID")

generate_url    = f"https://api.heygen.com/v2/template/{template_id}/generate"
#generate_url    = "https://api.heygen.com/v2/video/generate"

class QARequest(BaseModel):
    no: str
    question: str
    answer: str

class VideoResponse(BaseModel):
    status: str
    message: str
    video_url: str
    
    
    
def video_generator(title, script):
    
    payload = payload_setting(title, script)
    
    headers["Content-Type"] = "application/json"
    response = requests.post(generate_url, headers=headers, json=payload)
    if not response.json()["data"]:
        print(response)
        print(response.json()["error"])
        message = "Response Failed"
        
        return "", "error", message, ""
        

    video_id = response.json()["data"]["video_id"]
    print("video_id:", video_id)
    start_time = time.time()  # Track the start time
    
    # Check Video Generation Status
    video_status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    while True:
        response = requests.get(video_status_url, headers=headers)
        status = response.json()["data"]["status"]

        if status == "completed":
            video_url = response.json()["data"]["video_url"]
            
            message = 'Success'
            #thumbnail_url = response.json()["data"]["thumbnail_url"]
            # print(
            #     f"Video generation completed! \nVideo URL: {video_url} \nThumbnail URL: {thumbnail_url}"
            # )

            # Save the video to a file
            # video_filename = f"../../data/videos/{title}.mp4"
            # with open(video_filename, "wb") as video_file:
            #     video_content = requests.get(video_url).content
            #     video_file.write(video_content)
                
            return video_id, status, message, video_url

        elif status == "processing" or status == "pending":
            print("Video is still processing. Checking status...")
            time.sleep(10)  # Sleep for 5 seconds before checking again
            
            # Check if more than 20 minutes have passed
            if time.time() - start_time > 1200:
                print("Timeout: Video generation took too long.")
                message = 'Timeout Exceeded'
                return video_id, "timeout", message, ""
            
        elif status == "failed":
            error = response.json()["data"]["error"]
            print(f"Video generation failed. '{error}'")
            message = error
            
            return video_id, status, message, ""
    
    
@app.get("/")
async def root():
    return {"message": "API is ready!"}


@app.post("/generate_video", response_model=VideoResponse)
def generate_video(request: QARequest):
    # Process function logic goes here
    try:
        no = request.no 
        question = request.question
        answer = request.answer
        
        video_id, video_status, message, video_url = video_generator(no, answer)
        

        return VideoResponse(status = video_status, message = message, video_url=video_url)
    except Exception as e: 
        return VideoResponse(status = "error", message = "Backend Error", video_url="")
