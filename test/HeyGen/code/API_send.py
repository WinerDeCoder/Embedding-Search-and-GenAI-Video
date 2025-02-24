
import json
import requests
import pandas as pd
import os

# Đường dẫn đến file .xlsx
current_dir = os.getcwd()

# Navigate to folder `b` from folder `a`
path_to_b = os.path.join(current_dir, "../data")

# Example: Access a file in folder `b`
file_path = os.path.join(path_to_b, "small_number_questions.xlsx")

# Đọc file Excel vào DataFrame
df = pd.read_excel(file_path)

video_id_list = []

error_video = []

# Duyệt từng dòng trong DataFrame
for index, row in df.iterrows():
    try:
        print(f"Row {index}:")
        
        item_dict = row.to_dict()
        print(row.to_dict())  # Chuyển dòng thành dictionary để dễ xử lý
        
        url = "https://api.heygen.com/v2/video/generate"

        payload = {
            "caption": False,  # Caption, maybe the subtile
            "title": str(item_dict["STT"]),  # Need to change , match the index of video
            "callback_id": "string",
            "dimension": {
                "width": 1024,  # Fix
                "height": 720  # fix
            },
            "video_inputs": [      # up to 50, don't know whether it is video setting or many video at a time
                {
                    "character": {   # need to change to match  the avatar create
                        "type": "talking_photo",  # avatar (already) / talking_photo ( for custome photo)
                        "talking_photo_id": "fb3e19a8f9014884a40ee3b0ebf69c04",   # !!!!! extract
                        "scale": 1,
                        "offset": {
                            "x": 0,
                            "y": 0
                        }
                    },
                    "voice": {
                        "type": "text",
                        "voice_id": "c6fb81520dcd42e0a02be231046a8639", #str
                        "input_text": item_dict["Text"] #str
                    },   # voice id Fixx
                }
            ],
            "callback_url": "string"
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": "NWQ1ZGJhYjY5MGY0NGNmZDk1OWU0ZWUxNDU3YzY2YzYtMTcyNjIxNTM4Mg=="
        }

        response = requests.post(url, json=payload, headers=headers)

        print(response.text)
        
        covert_to_json =  json.loads(response.text)
        
        video_id = covert_to_json["data"]["video_id"]
        
        video_id_list +=  [{"STT": item_dict["STT"], "video_id": video_id}]
        
        print(video_id)
        
        
            
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        error_video += [{"STT": item_dict["STT"], "error": e}] 

if error_video:
    print("The following videos encountered errors and were not processed:")
    print(error_video)



import pickle
with open("pickle_storage/video_list_processing.pkl", "wb") as f:
    pickle.dump(video_id_list, f)
        
        
